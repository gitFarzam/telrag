from langchain_text_splitters import RecursiveCharacterTextSplitter
from typing import List
from huggingface_hub import InferenceClient
import openai
from openai import OpenAI
from openai.types.chat import ChatCompletion
from openai.types.responses.response import Response
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
import time

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

    def audio_to_text(self,file_path: str, model: str = constants.OPENAI_TRANSCRIPTION_MODEL) -> str:
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

class BooleanModel(BaseModel):
    result : bool


class LLM():
    """
    This is a class for using openai chat completion
    """
    # in-use: for intializing openai model
    def __init__(self,model):
        self.model = model
        self.client = OpenAI()
        return super().__init__()

    
    # in-use: for setting up openai model
    def setUp_openai_classifier(self,user_prompt,job):
        client = OpenAI()

        if job == 'categorizing':
            system_prompt = prompts.system_prompt_message_categorizer(
                            business_name=constants.BUSINESS_NAME,
                            business_description=constants.BUSINESS_DESCRIPTION
                            )
            schema = CategorzingModel.model_json_schema
            validator = CategorzingModel.model_validate_json
            json_schema_name = "CategorizingResponse"

        elif job == 'keyword_extraction':
            system_prompt = prompts.system_prompt_keyword_extractor()

            schema = KeywordModel.model_json_schema
            validator = KeywordModel.model_validate_json
            json_schema_name = "KeywordResponse"

        elif job == 'judge':
            system_prompt = prompts.SYSTEM_PROMPT_LLM_AS_JUDGE
            schema = BooleanModel.model_json_schema
            validator = BooleanModel.model_validate_json
            json_schema_name = "TrueFalseResponse"

        print(f"job: {job}")
        try:
            completion = client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                response_format={
                    "type": "json_schema",
                    "json_schema": {
                        "name": json_schema_name,
                        "schema": schema()
                    }
                },
                temperature=0
            )

            content = completion.choices[0].message.content
            result = validator(content).result
            return result
        
        except openai.RateLimitError as error:
            logger.error(error)


    def openai_text_generator(self,messages_history:list,new_messages:dict):
        """
        result is an instance of ChatCompletion 

        from openai.types.chat import ChatCompletion

        result = ChatCompletion
        content = result.choices[0].message.content
        completion_tokens = result.usage.completion_tokens
        prompt_tokens = result.usage.prompt_tokens
        
        """
        client = OpenAI()
        system_guideline = prompts.system_prompt_text_generator(business_name=constants.BUSINESS_NAME)
        system_message = {'role':'system','content':system_guideline}
        messages_history.insert(0,system_message)
        messages_history.append(new_messages)

        try:
            self.result =  client.chat.completions.create(
                model=self.model,  # or another supported model
                messages=messages_history
            )
            return self.result
        except openai.RateLimitError as error:
            logger.error(error)
        except openai.BadRequestError as error:
            logger.error(error)

    def openai_classifier(self,content,job):
        result = self.setUp_openai_classifier(content,job)
        return result

    def openai_text_rewriter(self,original_text:str):
        """
        Rewrites the provided text using OpenAI's API based on a specified tone/style.
        original_text: User's input query
        """
        try:
            # 2. Call the Responses API 
            response = self.client.responses.create(
                model=self.model,  # Highly cost-efficient for text manipulation tasks
                instructions=prompts.PROMPT_REWRITING_USER_QUERY,
                input=original_text
            )

            # 3. Extract and return the final rewritten text
            return response
            
        except Exception as e:
            return f"An error occurred: {e}"

            

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


    def embedder(self,model,text:str):
        client = InferenceClient(model=model,token=os.getenv("HF_API_TOKEN")) 
        embeddings = client.feature_extraction(text=text)
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
    def __init__(self,model,beta):
        from chat.services import hybrid_search,similar_category,fetch_content_from_document
        self.hybrid_search = hybrid_search
        self.similar_category = similar_category
        self.get_content = fetch_content_from_document

        self.beta = beta

        # Initialzing an instance of NLP class
        self.nlp = NLP()

        # openai keyword extractor
        self.llm = LLM(model)
        
    def llm_eval_df(self,test_data_path:str):
        return self.nlp.jsonl_reader(path=test_data_path)
    
    def retrieval_eval_df(self,test_data_path:str):
        # loading test data as a pandas dataframe
        return self.nlp.jsonl_reader(path=test_data_path)
    
    def llm_hallucination(self,test_data_path,top_k):
        
        df = self.llm_eval_df(test_data_path)

        for i, (index, row ) in enumerate(df.iterrows()):
            question = row['question']
            answer = row['answer']
            input_embedding = self.nlp.embedder(
                            model=constants.HF_EMBEDDING_MODEL,
                            text=[question]
                            )[0]
            hybrid_search_result = self.hybrid_search(
                            search_keyword=question, 
                            input_text_embedding=input_embedding,
                            top_k=top_k,
                            beta=self.beta
                            )
            print(f"---\n\nHR: {hybrid_search_result}\n\n---")
            
            # have all chunks from retreival here available and then send with question to an LLM and ask LLM is the answer correct or its producing wrong or doing hallucination, this can be done with a more advanced model.

            retrieval_context = "\n".join([self.get_content(embedding_obj.chunk.document)for embedding_obj in hybrid_search_result])
            
            result = self.llm.openai_text_generator(
                messages_history=[],
                new_messages={"role" : "user" , "content" : question}
            )

            result_content = result.choices[0].message.content

            # here an LLM as a Judge will compare 2 output with each other
            user_prompt = f"""
                - Question: {question}\n\n
                - Information Chunks: {retrieval_context} \n\n
                - Person Answer : {result_content}
                """
            judge_result = self.llm.openai_classifier(user_prompt,'judge')
            print(f"""
{user_prompt}\n
👨🏼‍⚖️ : {judge_result}\n\n-------------------\n
""")

            if index == 10:
                break

    def recall(self,top_k:int):
        self.top_k = top_k
        """
        Recall = Relevant Retrieved / Total Relevant
        """

    def precision(self,test_data_path:str,top_k:int):
        self.top_k = top_k
        df = self.retrieval_eval_df(test_data_path)
        """
        Precision = Relevant Retrieved / Total Retrieved
        """

        """
        I need to have hybrid_search here, hybrid search requires conversation object
        for all queries (prompts) in the dataframe hybrid search will be activated
        """

        all_categories = 0
        all_correct = 0
        total_relevant = 0
        total_first_correct = 0
        total_retrieval_iteration = 0
        for i, (index, row ) in enumerate(df.iterrows()):
            query = row['query']
            query_category = row['category']
            relevant_categories = self.similar_category(query_category)
            total_relevant += relevant_categories.__len__()
            result = self.hybrid_search(
                search_keyword=query, # alternatively: self.llm.openai_response(query,'keyword_extraction')[0] , # getting the first keyword
                # search_keyword=self.llm.openai_response(query,'keyword_extraction')[0] ,
                input_text_embedding=self.nlp.embedder(
                model=constants.HF_EMBEDDING_MODEL,
                chunks=[query]
                )[0],
                k=self.top_k,
                beta=self.beta
                )
            
            total_retrieval_iteration+=1
            
            categories = result.values_list('category',flat=True)
            first_category = categories.first()

            if query_category==first_category:
                total_first_correct+=1

            all_categories+=categories.__len__()

            correct_categories = 0
            for category in categories:
                if category==query_category:
                    correct_categories+=1 


            
            all_correct+=correct_categories
            print(f"""
Query Category: {query_category}
Categories: {categories}
total_relevant: {relevant_categories}({relevant_categories.__len__()})
correct_categories : {correct_categories}
\n------------------\n
                    """)

            # if index==20:
            #     break
        """
        note: this is basically wrong, because you have to count the document numbers and not the number of chunks
        
        """
        print(f"Precission@{self.top_k} (Relevant/Total Retrieved): {all_correct/all_categories}")

        print(f"Recall@{self.top_k} (Relevant/Total Relevant): {all_correct/total_relevant}")

        print(f"MAP@{self.top_k} (Total First Correct / Total Retrieval Iteration) : {total_first_correct/total_retrieval_iteration}")


def latency_calculator(before):
    after = time.time()
    return after-before


class ModelCost():
    def __init__(self,rag_component):
        """
        Costs are specified per model. By including the RAG component and its details, the pricing for the desired model can be retrieved.

        if the model name is not defined in the `COST_PER_TOKEN` dictionary, or no model is available for that component (like hubrid search which has None for the model) , False will be returned to tell that, no cost information is available!
        
        """
        rc_details = constants.RC_DETAILS
        self.cost_dict = constants.COST_PER_TOKEN
        self.rag_component = rag_component
        self.model = rc_details[rag_component]["model"]
        self.model_cost_dict = self.model_cost_dict_check()

    def cost_model_dispatcher(self):
        if self.model_cost_dict:
            if self.rag_component == constants.RAG_COMPONENTS["Text Generator"]:
                self.openai_chat_completion_cost()
            elif self.rag_component == constants.RAG_COMPONENTS["Query Rewriting"]:
                self.openai_response_cost()
            elif self.rag_component == constants.RAG_COMPONENTS["Message Categorizer"]:
                self.openai_message_categorizer_cost()
            elif self.rag_component == constants.RAG_COMPONENTS["Embedder"]:
                self.hf_embedding_cost()
        else:
            return False

    def model_cost_dict_check(self):
        """
        Check if cost data is available for the model or not
        """
        model_cost_dict:dict = self.cost_dict.get(self.model,{})
        if model_cost_dict is None:
            logger.error(f"Cost data is not available for {self.model}")
            return False
        
        return model_cost_dict


    def openai_chat_completion_cost(self,completion_result:ChatCompletion):

        prompt_tokens = completion_result.usage.prompt_tokens
        completion_tokens = completion_result.usage.completion_tokens
        input_cost = prompt_tokens * self.model_cost_dict["input"]
        output_cost = completion_tokens * self.model_cost_dict["output"]

        return {
            "unit" : self.model_cost_dict["unit"],
            "currency" : self.model_cost_dict["currency"],
            "input_cost" : input_cost,
            "output_cost" : output_cost
            }
    
    def openai_message_categorizer_cost(self,completion_result:ChatCompletion):
        pass
    
    def openai_response_cost(self,response:Response):
        input_tokens = response.usage.input_tokens
        output_tokens = response.usage.output_tokens
        input_cost = input_tokens * self.model_cost_dict["input"]
        output_cost = output_tokens * self.model_cost_dict["output"]

        return {
            "unit" : self.model_cost_dict["unit"],
            "currency" : self.model_cost_dict["currency"],
            "input_cost" : input_cost,
            "output_cost" : output_cost
            }

    def hf_embedding_cost(self):
        embedding_cost = self.model_cost_dict["embedding"]
        return {
            "unit" : self.model_cost_dict["unit"],
            "currency" : self.model_cost_dict["currency"],
            "embedding_cost" : embedding_cost,
            }



    