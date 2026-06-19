<<<<<<< HEAD
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
load_dotenv()

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
||||||| 6d2c1b6
=======
# Standard libraries imports
import os
import json
import time
from datetime import datetime
import logging

# Local imports
from .pydantic_classes import CategorzingModel,KeywordModel,BooleanModel
from .utils import Utils
import chat.constants as constants
import chat.prompts as prompts

# Installed libraries
from langchain_text_splitters import RecursiveCharacterTextSplitter
from huggingface_hub import InferenceClient
import openai
from openai import OpenAI
from openai.types.chat import ChatCompletion
from openai.types.responses.response import Response
from pydantic import ValidationError
from dotenv import load_dotenv
import pandas as pd

# Loading .env file variables
load_dotenv()

# Creating an instance of logging object
logger = logging.getLogger(__name__)


def latency_calculator(before):
    """
    This method is for detecting the duraction between 2 times, mostly for detecting llm models latency
    """
    after = time.time()
    return after-before


def audio_to_text(file_path: str, model: str = constants.OPENAI_TRANSCRIPTION_MODEL) -> str:
    """
    Converting audio to text
    """
    client = OpenAI() 

    with open(file_path, "rb") as audio_file:
        response = client.audio.transcriptions.create(
            model=model,
            file=audio_file
        )
    return response.text


def embedder(model,text:str):
    """
    Text embedder function
    """
    # Turning of INFO level log for hugging face logs
    info_logging = False

    if not info_logging:
        # 1. Suppress HTTP request and Hub logging
        logging.getLogger("httpx").setLevel(logging.ERROR)
        logging.getLogger("huggingface_hub").setLevel(logging.ERROR)

    client = InferenceClient(model=model,token=os.getenv("HF_API_TOKEN")) 
    embeddings = client.feature_extraction(text=text)
    return embeddings


class NLPToolKit(RecursiveCharacterTextSplitter):
    """
    Inheriting from langchain RecursiveCharacterTextSplitter, more methods can be added to this parent class
    """
    def __init__(self, separators = None, keep_separator = True, is_separator_regex = False, text=None, **kwargs):
        super().__init__(separators, keep_separator, is_separator_regex,  chunk_size = constants.CHUNK_SIZE,
        chunk_overlap = constants.CHUNK_OVERLAP,**kwargs)


class LLM():
    """
    This is a class for using LLM (openai) chat completion and responses
    """
    # in-use: for intializing openai model
    def __init__(self,model):
        self.model = model
        self.client = OpenAI()
        return super().__init__()
    

    def get_validator(self,job):
        """
        Getting the right class object for the corresponding job
        """

        if job == 'categorizing':
            return CategorzingModel.model_validate_json
        elif job == 'keyword_extraction':
            return KeywordModel.model_validate_json
        elif job == 'judge':
            return BooleanModel.model_validate_json
    
    
    def setUp_openai_classifier(self,user_prompt,job):
        """
        Setting up openai chat completion model which responsed are validated using schemas and pydantic classes
        """
        client = OpenAI()

        if job == 'categorizing':
            system_prompt = prompts.system_prompt_message_categorizer(
                            business_name=constants.BUSINESS_NAME,
                            business_description=constants.BUSINESS_DESCRIPTION
                            )
            schema = CategorzingModel.model_json_schema
            json_schema_name = "CategorizingResponse"

        elif job == 'keyword_extraction':
            system_prompt = prompts.system_prompt_keyword_extractor()

            schema = KeywordModel.model_json_schema
            json_schema_name = "KeywordResponse"

        elif job == 'judge':
            system_prompt = prompts.SYSTEM_PROMPT_LLM_AS_JUDGE
            schema = BooleanModel.model_json_schema
            json_schema_name = "TrueFalseResponse"

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
            return completion
        
        except openai.RateLimitError as error:
            logger.error(error)
        except ValidationError as error:
            logger.error(error)


    def openai_text_generator(self,messages_history:list,new_messages:dict):
        """
        regular openai chat completion model, without pydantic class, just for outputing pure text.
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
        """
        This method calls openai classifier and passes the job value
        """
        result = self.setUp_openai_classifier(content,job)
        return result

    def openai_text_rewriter(self,original_text:str):
        """
        Rewrites the provided text using OpenAI
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

            

class RagMetrics():
    def __init__(self,name,model,top_k,beta):

        # Beta and Top K have a range, so they should be validated beforehand
        self.beta = self.beta_validator(beta)
        self.top_k= self.top_k_validator(top_k)

        # Initialzing an instance of utils class
        self.utils = Utils()

        # openai keyword extractor
        self.llm = LLM(model)
        self.name = name

        # result path
        self.ret_result = constants.data_path(name,'ret_result')
        self.ret_result_history = constants.data_path(name,'ret_result_history')
        self.llm_result = constants.data_path(name,'llm_result')
        self.llm_result_history = constants.data_path(name,'llm_result_history')

        self.ret_test_data_path = constants.data_path(name,'test_retrieval_question')
        self.llm_test_data_path = constants.data_path(name,'llm_eval_qa')

    def beta_validator(self,beta):
        """
        This method checks the values for beta hyperparameter
        """
        if isinstance(beta, (int, float)):
            if beta >= 0 and beta <=1:
                return beta
            else:
                raise ValueError('Beta value should be between 0 and 1')
        else:
            raise ValueError('Beta value should be integer or float')

    def top_k_validator(self,top_k):
        """
        This method checks the values for top_k hyperparameter
        """
        if isinstance(top_k, (int)):
            if top_k >= 0 and top_k <=50:
                return top_k
            else:
                raise ValueError('top_k value should be between 1 and 50')
        else:
            raise ValueError('top_k value should be an integer')

        
    def llm_eval_df(self):
        """
        Getting LLM test dataset as a dataframe
        """
        self.llm_test_data_path
        file_path = self.llm_test_data_path
        try:
            return self.utils.jsonl_reader(path=file_path)
        except FileNotFoundError as e:
            # Turning of traceback message
            import sys
            sys.tracebacklimit = 0

            raise FileNotFoundError(f"File is not existed at this path: {file_path}\nError: {e}\n")
    
    def retrieval_eval_df(self):
        """
        Getting retrieval test dataset as a dataframe
        """
        file_path = self.ret_test_data_path
        try:
            return self.utils.jsonl_reader(path=file_path)
        except FileNotFoundError as e:
            # Turning of traceback message
            import sys
            sys.tracebacklimit = 0

            raise FileNotFoundError(f"File is not existed at this path: {file_path}\nError: {e}\n")
        

    def retrieveal_metrics(self):

        """
        Evaluating Retrieval component in RAG system.

        Precision = Relevant Retrieved / Total Retrieved
        Recall = Relevant Retrieved / Total Relevant
        MAP@ : Number of correct returns at the first rank

        This method iterate through all of the rows in the dataframe, and check the `category` value with the detected categories from retrieval and count the number of corrected matches
        """

        from chat.services import hybrid_search,similar_category
        import os

        # Retrieval Evaluation Test dataset
        df = self.retrieval_eval_df()


        all_categories = 0 # Overall categories were retrieved from retreival
        all_correct = 0 # Overall correct matches between test query category and retrieval queruies categories
        total_relevant = 0 # Number of all of the documents which have same value for the category with the user test queries category
        total_first_correct = 0
        total_retrieval_iteration = 0

        try:

            if os.path.isfile(self.ret_result):
                os.remove(self.ret_result)
                logger.info(f"Current result file: {self.ret_result} has been removed!")
        except OSError as e:
            print(e)

        with open(self.ret_result, "a", encoding="utf-8") as file:
            print(df)
            for i, (index, row ) in enumerate(df.iterrows()):
                # try except block for key error check!
                query = row['query'] # test query value (user query simulation, like a question)
                query_category = row['category'] # the corrected category for test query
                relevant_categories = similar_category(query_category) # number of all the documents in the database which have same category with test query category
                total_relevant += relevant_categories.__len__() # adding number of all relevant categories in each iteration to total number of relevant categories
                result = hybrid_search(
                    search_keyword=query, # alternatively: self.llm.openai_response(query,'keyword_extraction')[0] , # getting the first keyword
                    # search_keyword=self.llm.openai_response(query,'keyword_extraction')[0] ,
                    input_text_embedding=embedder(
                    model=constants.HF_EMBEDDING_MODEL,
                    text=[query]
                    )[0],
                    top_k=self.top_k,
                    beta=self.beta
                    ) # result from hybrid search, total number of similar embeddings
                
                total_retrieval_iteration+=1 # counting number of all retrievals
                
                categories = result.values_list('category',flat=True) # getting the category value for all retrieval outputs
                first_category = categories.first() # getting the category value for the first ranked output from retrieval

                if query_category==first_category:
                    total_first_correct+=1  # Counting the number of first correct prediction

                all_categories+=categories.__len__() # adding the number of all retrieved categories to all_categories variable

                # Counting the number of correct categories from the retriever output for each query insertion. The total number of available categories equals the top_k value in the retriever.
                correct_categories = 0
                for category in categories:
                    if category==query_category:
                        correct_categories+=1 

                all_correct+=correct_categories # adding the number of all correct categories matches to all_correct variabe

                print(f"""
                        Query Category: {query_category}
                        Categories: {categories}
                        total_relevant: {relevant_categories}({relevant_categories.__len__()})
                        correct_categories : {correct_categories}
                        \n------------------\n
                        """)

                if index==10:
                    break

                precision = all_correct/all_categories
                recall = all_correct/total_relevant
                map_at = total_first_correct/total_retrieval_iteration

                data = {'recall':recall,'precision':precision,'map':map_at}
                file.write(json.dumps(data) + "\n")
        """
        note: this is basically wrong, because you have to count the document numbers and not the number of chunks
        
        """
        
        result_history = {
            'top_k':self.top_k,
            'beta' : self.beta ,
            'precision' : precision,
            'recall' : recall,
            'map_at' : map_at,
            'time' : datetime.now().replace(microsecond=0).__str__()
            }

        # Creating new result history file
        with open(self.ret_result_history,"a",encoding="utf-8") as file:
            file.write(json.dumps(result_history) +'\n')

        logger.info("New result history file has been created!")


        print(f"Precission@{self.top_k} (Relevant/Total Retrieved): {precision}")

        print(f"Recall@{self.top_k} (Relevant/Total Relevant): {recall}")

        print(f"MAP@{self.top_k} (Total First Correct / Total Retrieval Iteration) : {map_at}")


    def llm_hallucination(self):
        """
        This method is for checking if the the llm hallucinates or no. test dataset includes lines of question-answer pairs plus category name and the related document, an example:

        {"question": "Where can customers find TelMart associates to help with purchases?", "answer": "TelMart associates are available at staffed checkout lanes throughout the store to assist customers with their purchases.", "category": "checkout_support", "file_name": "cashier_help.txt"}

        each embedding
        """
        from chat.services import hybrid_search,fetch_content_from_document

        # Retrieval Evaluation Test dataset
        df = self.llm_eval_df()

        # Number of total queryies which is passed to the llm
        total_query = 0

        # number of all True responses from Judge LLM
        total_true = 0


        try:
            if os.path.isfile(self.llm_result):
                os.remove(self.llm_result)
                logger.info(f"Current result file: {self.llm_result} has been removed!")
        except OSError as e:
            print(e)

        with open(self.llm_result, "a", encoding="utf-8") as file:
            for i, (index, row ) in enumerate(df.iterrows()):
                question = row['question']
                answer = row['answer']
                input_embedding = embedder(
                                model=constants.HF_EMBEDDING_MODEL,
                                text=[question]
                                )[0]
                hybrid_search_result = hybrid_search(
                                search_keyword=question, 
                                input_text_embedding=input_embedding,
                                top_k=self.top_k,
                                beta=self.beta
                                )
                # print(f"---\n\nHR: {hybrid_search_result}\n\n---")
                
                # have all chunks from retreival here available and then send with question to an LLM and ask LLM is the answer correct or its producing wrong or doing hallucination, this can be done with a more advanced model.

                retrieval_context = "\n".join([fetch_content_from_document(embedding_obj.chunk.document)for embedding_obj in hybrid_search_result])
                
                # Passing test query to llm which is used for rag system
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
                validator = self.llm.get_validator('judge')
                judge_result  = validator(judge_result.choices[0].message.content).result
                print(f"""👨🏼‍⚖️ : {judge_result}""")
                

                total_query+=1
                if judge_result:
                    total_true+=1

                accuracy = total_true/total_query

                data = {'accuracy':accuracy}
                file.write(json.dumps(data) + "\n")

                if index == 10:
                    break

        
        data_history = {
            'top_k':self.top_k,
            'beta' : self.beta ,
            'accuracy' : accuracy,
            'time' : datetime.now().replace(microsecond=0).__str__()
            }

        # Creating new result history file
        with open(self.llm_result_history,"a",encoding="utf-8") as file:
            file.write(json.dumps(data_history) +'\n')

        return accuracy



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

    def cost_model_dispatcher(self,data):
        if self.model_cost_dict:
            if self.rag_component == constants.RAG_COMPONENTS["Text Generator"]:
                return self.openai_chat_completion_cost(data['completion'])
            elif self.rag_component == constants.RAG_COMPONENTS["Query Rewriting"]:
                return self.openai_response_cost(data['response'])
            elif self.rag_component == constants.RAG_COMPONENTS["Message Categorizer"]:
                return self.openai_chat_completion_cost(data['completion'])
            elif self.rag_component == constants.RAG_COMPONENTS["Embedder"]:
                return self.hf_embedding_cost()
        else:
            return False

    def model_cost_dict_check(self):
        """
        Check if cost data is available for the model or not
        """
        model_cost_dict:dict = self.cost_dict.get(self.model,{})
        if model_cost_dict is None:
            logger.error(f"Cost data is not available for {self.rag_component}")
            return False
        
        return model_cost_dict


    def openai_chat_completion_cost(self,completion_result:ChatCompletion):

        prompt_tokens = completion_result.usage.prompt_tokens
        completion_tokens = completion_result.usage.completion_tokens
        input_cost = prompt_tokens * (self.model_cost_dict["input"]/self.model_cost_dict["unit"])
        output_cost = completion_tokens * (self.model_cost_dict["output"]/self.model_cost_dict["unit"])


        return {
            "currency" : self.model_cost_dict["currency"],
            "input_cost" : input_cost,
            "output_cost" : output_cost
            }
    
    def openai_response_cost(self,response:Response):
        input_tokens = response.usage.input_tokens
        output_tokens = response.usage.output_tokens
        input_cost = input_tokens * (self.model_cost_dict["input"]/self.model_cost_dict["unit"])
        output_cost = output_tokens * (self.model_cost_dict["output"]/self.model_cost_dict["unit"])

        logger.info(f"response cost --><-->: {input_cost}")

        return {
            "currency" : self.model_cost_dict["currency"],
            "input_cost" : input_cost,
            "output_cost" : output_cost
            }

    def hf_embedding_cost(self):
        embedding_cost = self.model_cost_dict["embedding"]
        return {
            "currency" : self.model_cost_dict["currency"],
            "embedding_cost" : embedding_cost,
            }


>>>>>>> demo
