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
import numpy as np
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
    """
    This class if made for evaluating retrieval performance, it gets multiple test query and will compare them with oberserved query, both queryies belong to a unique category, if categories were matched together, it means that retrieval worked properly with providing right documents @k

    test_query : jsonl file, will compite to dict: sample: {"query": "TelBurger submits refund requests immediately after approval", "category": "crm_support"}
    observed_query : fetches from database by retrieval and compiles as a dictionary like above
    k : a positive integer number will determine how many documents have to be retrieved from database
    """
    def __init__(self,embedding_model,input_queries, observed_query):
        self.model = embedding_model
        self.input_queries = input_queries
        self.observed_query = observed_query

    def text_strip(text:str):
        return text.strip()

    def embedder(self,chunks:list):
        client = InferenceClient(model=self.model,token=os.getenv("HF_API_TOKEN")) 
        embeddings = client.feature_extraction(text=chunks)
        return embeddings
    
    def cosine_similarity(v1, array_of_vectors): 
        """
        Cosine similarity between a vector and either a single vector (1D) or an array of vectors (2D).
        Returns a float for 1D input, or a list of floats for 2D input.
        """
        v1 = np.asarray(v1, dtype=np.float32).ravel() # ravel converts multi dimensional into 1 dimensional

        A = np.asarray(array_of_vectors, dtype=np.float32)

        if A.ndim == 1:
            A = A.ravel()
            denom = np.linalg.norm(v1) * np.linalg.norm(A)
            return float(0.0 if denom == 0 else np.dot(v1, A) / denom)

        # 2D case: compute similarities for each row in A
        A = np.atleast_2d(A)
        v1_norm = np.linalg.norm(v1)
        A_norms = np.linalg.norm(A, axis=1)
        denom = v1_norm * A_norms
        with np.errstate(divide='ignore', invalid='ignore'):
            sims = (A @ v1) / np.where(denom == 0, 1.0, denom)
        sims[denom == 0] = 0.0
        return sims.tolist()


    def top_k_greatest_indices(lst, k):
        """
        Get the indices of the top k greatest items in a list.

        Parameters:
        lst (list): The list of elements to evaluate.
        k (int): The number of top elements to retrieve by index.

        Returns:
        list: A list of indices corresponding to the top k greatest elements in lst.
        """
        # Enumerate the list to keep track of indices
        indexed_list = list(enumerate(lst))
        # Sort by element values in descending order
        sorted_by_value = sorted(indexed_list, key=lambda x: x[1], reverse=True)
        # Extract the top k indices
        top_k_indices = [index for index, value in sorted_by_value[:k]]
        return top_k_indices



    def metrics_computation(self,k):
        # Normalize all embeddings to NumPy once (input is conidered as tensors, if not, just create array from list)
        embeddings = self.embedder()
        np_embeddings = []
        for x in embeddings:
            if hasattr(x, "detach"):  # torch tensor
                x = x.detach().cpu().numpy()
            np_embeddings.append(np.asarray(x, dtype=np.float32).ravel())

        E = np.vstack(np_embeddings) #flatenning all embeddings

        for i in self.input_queries:
            query = self.text_strip(i['query'])
            category = i['category']

            query_embedding = self.embedder([query])[0]

            # Cosine Similarity
            cosine_scores = self.cosine_similarity(query_embedding,E)
            top_results = self.top_k_greatest_indices(cosine_scores,k)



