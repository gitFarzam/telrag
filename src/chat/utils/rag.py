from langchain_text_splitters import RecursiveCharacterTextSplitter
from typing import List
from huggingface_hub import InferenceClient
import openai
from openai import OpenAI
from pydantic import BaseModel,Field
from typing import Literal
from dotenv import load_dotenv
from enum import IntEnum
import os
import json
from django.conf import settings
import chat.constants as constants
import chat.prompts as prompts
import numpy as np
import logging
import pandas as pd

load_dotenv()
logger = logging.getLogger(__name__)

class NLPToolKit(RecursiveCharacterTextSplitter):
    def __init__(self, separators = None, keep_separator = True, is_separator_regex = False, text=None, **kwargs):
        super().__init__(separators, keep_separator, is_separator_regex,  chunk_size = constants.CHUNK_SIZE,
        chunk_overlap = constants.CHUNK_OVERLAP,**kwargs)

    # in-use: for generating embedding for sentences
    def embedder(self,chunks:list,model=constants.HF_EMBEDDING_MODEL):
        client = InferenceClient(model=model,token=os.getenv("HF_API_TOKEN")) 
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

class KeywordModel(BaseModel):
    result: List[str] = Field(
        ...,
        min_length=2,
        max_length=5
    )

class HuggingFaceModel:
    def __init__(self, hf_model: str, hf_token: str):
        self.hf_model = hf_model
        self.hf_token = hf_token

        self.client = InferenceClient(
            model=self.hf_model,
            token=self.hf_token
        )

class HuggingFaceModel:
    def __init__(self, hf_model: str, hf_token: str):
        self.hf_model = hf_model
        self.hf_token = hf_token

        self.client = InferenceClient(
            model=self.hf_model,
            token=self.hf_token
        )

    def setup_hf_detector(self, system_prompt: str, user_prompt: str):

        prompt = f"""
                {system_prompt}

                User:
                {user_prompt}

                Return ONLY valid JSON in this exact format:
                {{
                    "result": [
                        "keyword1",
                        "keyword2",
                        "keyword3",
                        "keyword4",
                        "keyword5"
                    ]
                }}
                """

        completion = self.client.text_generation(
            prompt=prompt,
            max_new_tokens=120,
            temperature=0.1,
            return_full_text=False
        )

        # Parse JSON string
        data = json.loads(completion)

        # Validate with Pydantic
        validated = KeywordModel(**data)

        return validated.result


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

        try:
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
            result = CategorzingModel.model_validate_json(content).result
            return result
        
        except openai.RateLimitError as error:
            logger.error(error)


    def openai_text_generator(self,messages_history:list,new_messages:dict):
        client = OpenAI()
        system_guideline = prompts.system_prompt_text_generator(business_name=constants.BUSINESS_NAME)
        system_message = {'role':'system','content':system_guideline}
        messages_history.insert(0,system_message)
        messages_history.append(new_messages)

        try:
            result =  client.chat.completions.create(
                model=self.openai_model,  # or another supported model
                messages=messages_history
            ).choices[0].message.content

            return result
        except openai.RateLimitError as error:
            logger.error(error)

        
    # in-use: for categorzing message
    def message_categorizer(self,content) -> int:
        system_prompt = prompts.system_prompt_message_categorizer(
            business_name=constants.BUSINESS_NAME,
            business_description=constants.BUSINESS_DESCRIPTION
            )
        result = self.setUp_openai_detector(system_prompt, content)
        return result
    

class NLP():
    """
    This class if made for evaluating retrieval performance, it gets multiple test query and will compare them with oberserved query, both queryies belong to a unique category, if categories were matched together, it means that retrieval worked properly with providing right documents @k

    test_query : jsonl file, will compite to dict: sample: {"query": "TelBurger submits refund requests immediately after approval", "category": "crm_support"}
    observed_query : fetches from database by retrieval and compiles as a dictionary like above
    k : a positive integer number will determine how many documents have to be retrieved from database

    Steps:
        1. Assigning an embedding model
        2. having the path for input_queries ready
        3. creating {'query':'embedding','category':'value'} for oberserved_query, by annotating Embedding model object
        4. seprating vector embeddings from Embedding model as an numpy 2D array from categories as a different list
        5. creating an embedding and category from test data as well, storing in the database
        6. measuring hybrid search function by considering these values
    """
    def __init__(self):
        return super().__init__()

    def text_strip(text:str):
        return text.strip()
    
    def jsonl_reader(self,path)->pd.DataFrame:
        """
        jsonL works fine with large data, as its possible to stream it and no need to load all at once. (for big size using yield for streaming)
        """

        with open(path) as f:
            return pd.DataFrame([json.loads(line) for line in f])
        

    def value_checker(self,df:pd.DataFrame,test_raw_path):
        """
        This method will check are all keys from source data (category and file_name) existed in the dataframe or not
        """
        unique_categories = sorted(df['category'].unique().tolist())
        unique_files = sorted(df['file_name'].unique().tolist())
        
        categories = sorted([dir.name for dir in os.scandir(test_raw_path) if dir.is_dir()])
        files=[]
        for category in categories:
            files +=[f for f in os.listdir(os.path.join(test_raw_path,category)) if f.endswith('.txt')]
        
        files = sorted(files)

        
        if unique_files == files and unique_categories == categories:
            return True
        else:
            print("there is a mismatch: unique_categories, categories , unique_files , files -> \n\n" , 
                        f"{unique_categories}\n\n{categories}\n\n{unique_files}\n\n{files}"
                    )
            return False


    def embedder(self,model,chunks:list):
        client = InferenceClient(model=model,token=os.getenv("HF_API_TOKEN")) 
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



class RagMetrics():
    def __init__(self,test_data_path:str):
        from chat.services import hybrid_search
        self.hybrid_search = hybrid_search

        # Initialzing an instance of NLP class
        self.nlp = NLP()

        # loading test data as a pandas dataframe
        self.df = self.nlp.jsonl_reader(path=test_data_path)

    def recall(self):
        """
        Recall = Relevant Retrieved / Total Relevant
        """

    def precision(self):
        """
        Precision = Relevant Retrieved / Total Retrieved
        """

        """
        I need to have hybrid_search here, hybrid search requires conversation object
        for all queries (prompts) in the dataframe hybrid search will be activated
        """
        k = 5 # top k document
        all_categories = 0
        all_correct = 0
        for index, row in self.df.iterrows():
            query = row['query']
            query_category = row['category']
            result = self.hybrid_search(
                search_keyword=query,
                input_text_embedding=self.nlp.embedder(
                model=constants.HF_EMBEDDING_MODEL,
                chunks=[query]
                )[0],
                k=k
                )
            
            categories = list(result.values_list('category',flat=True))
            all_categories+=categories.__len__()

            correct_categories = 0
            for category in categories:
                if category==query_category:
                    correct_categories+=1 
            all_correct+=correct_categories

            print(categories , query_category , '\n----\n')

        """
        note: this is basically wrong, because you have to count the document numbers and not the number of chunks
        
        """
        print(f"Precission@{k} (Relevant/Total Retrieved): {all_correct/all_categories}")
