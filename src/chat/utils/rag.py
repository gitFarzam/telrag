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
load_dotenv(settings.ENV_PATH)

class RAGToolKit(RecursiveCharacterTextSplitter):

    def __init__(self, separators = None, keep_separator = True, is_separator_regex = False, text=None, **kwargs):
        super().__init__(separators, keep_separator, is_separator_regex,  chunk_size = 4000,
        chunk_overlap = 200,**kwargs)


    def embedder(self,chunks:list):
        client = InferenceClient(model="sentence-transformers/all-MiniLM-L6-v2" , token="hf_Gd3Gg0o75RfKG3IplnjVKC2tJulngVtKf5") 
        embedding = client.feature_extraction(text=chunks)
        return embedding


    def text_generator(self,messages_history:list,new_messages:dict):
        system_guideline = "You are a live agent customer service from Lumiere Beauty, which is a full-service online beauty retailer dedicated to providing high-quality skincare, makeup, haircare, and wellness products to customers across the United States and selected international markets."

        system_message = {'role':'system','content':system_guideline}
        messages_history.insert(0,system_message)
        messages_history.append(new_messages)

        # print(f'------\n\n {messages_history} \n\n---------')

        client = InferenceClient(model="openai/gpt-oss-20b" , token="hf_Gd3Gg0o75RfKG3IplnjVKC2tJulngVtKf5") 
        return client.chat_completion(messages=messages_history).choices[0].message.content
    

    def openai_text_generator(self,messages_history:list,new_messages:dict):
        

        client = OpenAI()

        system_guideline = "You are a live agent customer service from Lumiere Beauty, which is a full-service online beauty retailer dedicated to providing high-quality skincare, makeup, haircare, and wellness products to customers across the United States and selected international markets."

        system_message = {'role':'system','content':system_guideline}
        messages_history.insert(0,system_message)
        messages_history.append(new_messages)


        return client.chat.completions.create(
            model="gpt-4.1-mini",  # or another supported model
            messages=messages_history
        ).choices[0].message.content


    def audio_to_text(self,file_path: str, model: str = "whisper-1") -> str:
        client = OpenAI()  # Make sure OPENAI_API_KEY is set in env

        with open(file_path, "rb") as audio_file:
            response = client.audio.transcriptions.create(
                model=model,
                file=audio_file
            )
        
        # response.text contains the transcription
        return response.text



class TrueFalseModel(BaseModel):
    result : bool


class CategorzingModel(BaseModel):
    result: Literal[0, 1, 2, 3]


class IntentType(IntEnum):
    GREETING = 0
    GENERAL_INQUIRY = 1
    PII_SUBMISSION = 2
    PRODUCT_INFO = 3
    ORDER = 4
    SHIPPING = 5
    RETURN_REFUND = 6
    ACCOUNT = 7
    PAYMENT = 8
    PROMOTION = 9
    COMPLAINT = 10
    SAFETY = 11
    BUSINESS = 12
    TECHNICAL = 13
    ESCALATION = 14
    NONE = 15


class IntegerModel(BaseModel):
    result: IntentType



class RetirievalNavigator():
    """
    import paydantic
    then -> write a class which returns True and False (to check if it's greeting or no):

        if it's greeting, answering with one of the pre-ready answers.
        if not -> go for similarity scores
            provide context for another function which detects if contexts are good for answering or no (requires another True False passing for a pydantic)
            (this can be replaced with a threshhold for similarity scores , or a hubrid approach)
            if it's the anwer : send context to agent
            if not -> sending to telegram
                again here should pass through similarity gate
            
    """
    def __init__(self,model,token):
        self.model = model
        self.token = token
        return super().__init__()
    
    def greeting_classifier(self,text):
        client = InferenceClient(model=self.model,token=self.token)
        self.classifier = client.text_classification
        prompted_text = f"This sentence is about greeting: {text}"
        return self.classifier(text=prompted_text)
    
    
    def setUp_detector(self,system_prompt,user_prompt):
        client = InferenceClient(model=self.model,token=self.token)

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



    def setUp_openai_detector(self,system_prompt,user_prompt):
        client = OpenAI()

        completion = client.chat.completions.create(
            model="gpt-4.1-mini",
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

    def message_categorizer(self,content) -> int:
        system_prompt = f"""
            You are an AI tasked with evaluating how well a user's question can be answered using a set of provided information.
            Your job is to compare the user's question with the provided information and classify it into one of four categories:
            Category 0: The provided information is directly related to the question, and the question can be fully answered using it.\n
            Category 1: The provided information is not required to answer the question (for example, greetings, general questions, or requests unrelated to the information). The question can be answered without it.
            Category 2: The provided information is somewhat related, but insufficient to confidently answer the question.\n
            Category 3: The question is completely outside the scope of the provided information; the information is unrelated or irrelevant.\n\n
            Rules:
            Do not use any external knowledge beyond what is explicitly provided.
            Always classify strictly based on the comparison between the provided information and the user's question.
            Do not provide explanations or reasoning.
            Return only the category number: 0, 1, 2, or 3.
        """
        return self.setUp_openai_detector(system_prompt, content)
