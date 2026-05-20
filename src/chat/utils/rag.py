from langchain_text_splitters import RecursiveCharacterTextSplitter
from typing import List
from langchain_core.documents.base import Document
from huggingface_hub import InferenceClient
from openai import OpenAI
from pydantic import BaseModel
from typing import Literal
from dotenv import load_dotenv
from enum import IntEnum
import os
from django.conf import settings
import chat.constants as constants
import chat.prompts as prompts
load_dotenv()

class NLPToolKit(RecursiveCharacterTextSplitter):
    def __init__(self, separators = None, keep_separator = True, is_separator_regex = False, text=None, **kwargs):
        super().__init__(separators, keep_separator, is_separator_regex,  chunk_size = constants.CHUNK_SIZE,
        chunk_overlap = constants.CHUNK_OVERLAP,**kwargs)

    # in-use: for generating embedding for sentences
    def embedder(self,chunks:list):
        client = InferenceClient(model=constants.HF_EMBEDDING_MODEL,token=os.getenv("HF_API_TOKEN")) 
        embedding = client.feature_extraction(text=chunks)
        return embedding

    def audio_to_text(self,file_path: str, model: str = "whisper-1") -> str:
        client = OpenAI()  # Make sure OPENAI_API_KEY is set in env

        with open(file_path, "rb") as audio_file:
            response = client.audio.transcriptions.create(
                model=model,
                file=audio_file
            )
        return response.text


class CategorzingModel(BaseModel):
    result: Literal[0, 1, 2, 3]


class RetrievalToolKit():
    """
    This is a class for using openai chat completion
    """
    # in-use: for intializing openai model
    def __init__(self,hf_model=None,hf_token=None,openai_model=None):
        self.hf_model = hf_model
        self.hf_token = hf_token
        self.openai_model = openai_model
        return super().__init__()
    

    def setUp_hf_detector(self,system_prompt,user_prompt):
        client = InferenceClient(model=self.hf_model,token=self.hf_token)

        completion = client.chat_completion(
            model="meta-llama/Llama-3.1-8B-Instruct",  # or another compatible model
            messages=[
                {"role": "system", "content": system_prompt},
                {"role" : "user" , "content" : user_prompt}
            ],
            response_format={
                "type": "json_schema",
                "json_schema": {
                    "name": "TrueFalseResponse",
                    "strict": True,
                    "schema": CategorzingModel.model_json_schema()
                }
            }
    )
        return CategorzingModel.model_validate_json(completion.choices[0].message.content).result

    
    # in-use: for setting up openai model
    def setUp_openai_detector(self,system_prompt,user_prompt):
        client = OpenAI()

        completion = client.chat.completions.create(
            model=self.openai_model,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            response_format={
                "type": "json_schema",
                "json_schema": {
                    "name": "CategorizingResponse",
                    "schema": CategorzingModel.model_json_schema()
                }
            },
            temperature=0
        )

        content = completion.choices[0].message.content

        return CategorzingModel.model_validate_json(content).result
    

    def openai_text_generator(self,messages_history:list,new_messages:dict):
        client = OpenAI()
        system_guideline = prompts.system_prompt_text_generator(business_name=constants.BUSINESS_NAME)
        system_message = {'role':'system','content':system_guideline}
        messages_history.insert(0,system_message)
        messages_history.append(new_messages)


        return client.chat.completions.create(
            model=self.openai_model,  # or another supported model
            messages=messages_history
        ).choices[0].message.content
    

    # in-use: for categorzing message
    def message_categorizer(self,content) -> int:
        system_prompt = prompts.system_prompt_message_categorizer(
            business_name=constants.BUSINESS_NAME,
            business_description=constants.BUSINESS_DESCRIPTION
            )
        return self.setUp_openai_detector(system_prompt, content)
    

class RetrievalEvaluator():
    def __init__(self,input_data, target_data):
        pass