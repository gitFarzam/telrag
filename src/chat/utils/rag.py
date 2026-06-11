from langchain_text_splitters import RecursiveCharacterTextSplitter
from huggingface_hub import InferenceClient
import openai
from openai import OpenAI
from openai.types.chat import ChatCompletion
from openai.types.responses.response import Response
from pydantic import ValidationError
from dotenv import load_dotenv
import os
import json
import chat.constants as constants
import chat.prompts as prompts
import logging
import pandas as pd
import time
from datetime import datetime
from .pydantic_classes import CategorzingModel,KeywordModel,BooleanModel


load_dotenv()
logger = logging.getLogger(__name__)


def latency_calculator(before):
    after = time.time()
    return after-before


def audio_to_text(self,file_path: str, model: str = constants.OPENAI_TRANSCRIPTION_MODEL) -> str:
    client = OpenAI()  # Make sure OPENAI_API_KEY is set in env

    with open(file_path, "rb") as audio_file:
        response = client.audio.transcriptions.create(
            model=model,
            file=audio_file
        )
    return response.text


def embedder(model,text:str):
    # Turning of INFO level log for hugging face
    info_logging = False

    if not info_logging:
        # 1. Suppress HTTP request and Hub logging
        logging.getLogger("httpx").setLevel(logging.ERROR)
        logging.getLogger("huggingface_hub").setLevel(logging.ERROR)

    client = InferenceClient(model=model,token=os.getenv("HF_API_TOKEN")) 
    embeddings = client.feature_extraction(text=text)
    return embeddings


class NLPToolKit(RecursiveCharacterTextSplitter):
    def __init__(self, separators = None, keep_separator = True, is_separator_regex = False, text=None, **kwargs):
        super().__init__(separators, keep_separator, is_separator_regex,  chunk_size = constants.CHUNK_SIZE,
        chunk_overlap = constants.CHUNK_OVERLAP,**kwargs)


class LLM():
    """
    This is a class for using openai chat completion
    """
    # in-use: for intializing openai model
    def __init__(self,model):
        self.model = model
        self.client = OpenAI()
        return super().__init__()
    

    def get_validator(self,job):

        if job == 'categorizing':
            return CategorzingModel.model_validate_json
        elif job == 'keyword_extraction':
            return KeywordModel.model_validate_json
        elif job == 'judge':
            return BooleanModel.model_validate_json
    
    
    # in-use: for setting up openai model
    def setUp_openai_classifier(self,user_prompt,job):
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

            

class Utils():
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

class RagMetrics():
    def __init__(self,model,top_k,beta):

        self.top_k=top_k
        self.beta = beta

        # Initialzing an instance of utils class
        self.utils = Utils()

        # openai keyword extractor
        self.llm = LLM(model)
        
    def llm_eval_df(self,test_data_path:str):
        return self.utils.jsonl_reader(path=test_data_path)
    
    def retrieval_eval_df(self,test_data_path:str):
        # loading test data as a pandas dataframe
        return self.utils.jsonl_reader(path=test_data_path)
    
    def result_df(self,name:str):
        
        return {
            'ret_result_df':self.utils.jsonl_reader(path=constants.data_path(name)['result']),
            'ret_result_history_df' : self.utils.jsonl_reader(path=constants.data_path(name)['result_history']),
            'llm_result_df':self.utils.jsonl_reader(path=constants.data_path(name)['llm_result']),
            'llm_result_history_df' : self.utils.jsonl_reader(path=constants.data_path(name)['result_llm_history'])
        }

    def retrieveal_metrics(self,test_data_path:str):
        from chat.services import hybrid_search,similar_category
        import os

        df = self.retrieval_eval_df(test_data_path)
        """
        Precision = Relevant Retrieved / Total Retrieved
        Recall = Relevant Retrieved / Total Relevant
        MAP@ : Number of correct returns at the first rank

        This method iterate through all of the rows in the dataframe, and check the `category` value with the detected categories from retrieval and count the number of corrected matches
        """

        all_categories = 0 # Overall categories were retrieved from retreival
        all_correct = 0 # Overall correct matches between test query category and retrieval queruies categories
        total_relevant = 0 # Number of all of the documents which have same value for the category with the user test queries category
        total_first_correct = 0
        total_retrieval_iteration = 0

        result_file_path = constants.data_path('telmart')['result']
        
        try:

            if os.path.isfile(result_file_path):
                os.remove(result_file_path)
                logger.info(f"Current result file: {result_file_path} has been removed!")
        except OSError as e:
            print(e)

        with open(result_file_path, "a", encoding="utf-8") as file:
            for i, (index, row ) in enumerate(df.iterrows()):
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

                if index==30:
                    break

                precision = all_correct/all_categories
                recall = all_correct/total_relevant
                map_at = total_first_correct/total_retrieval_iteration

                data = {'recall':recall,'precision':precision,'map':map_at}
                file.write(json.dumps(data) + "\n")
        """
        note: this is basically wrong, because you have to count the document numbers and not the number of chunks
        
        """
        result_history_file_path = constants.data_path('telmart')['result_history']
        
        result_history = {
            'top_k':self.top_k,
            'beta' : self.beta ,
            'precision' : precision,
            'recall' : recall,
            'map_at' : map_at,
            'time' : datetime.now().replace(microsecond=0).__str__()
            }

        # Creating new result history file
        with open(result_history_file_path,"a",encoding="utf-8") as file:
            file.write(json.dumps(result_history) +'\n')

        logger.info("New result history file has been created!")


        print(f"Precission@{self.top_k} (Relevant/Total Retrieved): {precision}")

        print(f"Recall@{self.top_k} (Relevant/Total Relevant): {recall}")

        print(f"MAP@{self.top_k} (Total First Correct / Total Retrieval Iteration) : {map_at}")


    def llm_hallucination(self,test_data_path):
        """
        This method is for checking if the the llm hallucinates or no. test dataset includes lines of question-answer pairs plus category name and the related document, an example:

        {"question": "Where can customers find TelMart associates to help with purchases?", "answer": "TelMart associates are available at staffed checkout lanes throughout the store to assist customers with their purchases.", "category": "checkout_support", "file_name": "cashier_help.txt"}

        each embedding
        """
        from chat.services import hybrid_search,fetch_content_from_document

        df = self.llm_eval_df(test_data_path)

        # Number of total queryies which is passed to the llm
        total_query = 0

        # number of all True responses from Judge LLM
        total_true = 0

        llm_result_file_path = constants.data_path('telmart')['llm_result']
        

        try:

            if os.path.isfile(llm_result_file_path):
                os.remove(llm_result_file_path)
                logger.info(f"Current result file: {llm_result_file_path} has been removed!")
        except OSError as e:
            print(e)

        with open(llm_result_file_path, "a", encoding="utf-8") as file:
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

        result_llm_history_file_path = constants.data_path('telmart')['result_llm_history']
        
        data_history = {
            'top_k':self.top_k,
            'beta' : self.beta ,
            'accuracy' : accuracy,
            'time' : datetime.now().replace(microsecond=0).__str__()
            }

        # Creating new result history file
        with open(result_llm_history_file_path,"a",encoding="utf-8") as file:
            file.write(json.dumps(data_history) +'\n')

        return accuracy
    
    def visualization(self,name):
        import matplotlib.pyplot as plt

        # try:
        dfs = self.result_df(name)
        ret_result_df = dfs['ret_result_df']
        ret_result_history_df = dfs['ret_result_history_df']
        llm_result_df = dfs['llm_result_df']
        llm_result_history_df = dfs['llm_result_history_df']


        print(f"Result:\n{ret_result_df}\n\n---\n\nResult History:\n{ret_result_history_df} ")

        plot_path = constants.data_path('telmart')['result_plots']
        if not os.path.exists(plot_path):
            os.mkdir(plot_path)


        for colum in ret_result_df.columns.to_list():
            plt.plot(ret_result_df[colum.__str__()])

        for colum in llm_result_df.columns.to_list():
            plt.plot(llm_result_df[colum.__str__()])

        plt.savefig(f"{plot_path}/retrieval.png", dpi=300, bbox_inches='tight')

        # recall plot

        # except Exception as e:
        #     message = f"Error in creating dataframes for {name} : {e}"
        #     logger.error(message)

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


