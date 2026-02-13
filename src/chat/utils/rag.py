from langchain_text_splitters import RecursiveCharacterTextSplitter
from typing import List
from langchain_core.documents.base import Document
from huggingface_hub import InferenceClient
from pydantic import BaseModel
from dotenv import load_dotenv

load_dotenv()

class RAGToolKit(RecursiveCharacterTextSplitter):

    def __init__(self, separators = None, keep_separator = True, is_separator_regex = False, text=None, **kwargs):
        super().__init__(separators, keep_separator, is_separator_regex,  chunk_size = 4000,
        chunk_overlap = 200,**kwargs)


    def embedder(self,chunks:list):
        client = InferenceClient(model="sentence-transformers/all-MiniLM-L6-v2" , token="hf_Gd3Gg0o75RfKG3IplnjVKC2tJulngVtKf5") 
        embedding = client.feature_extraction(text=chunks)
        return embedding


    def text_generator(self,messages_history,new_messages:dict):
        system_guideline = "You are a live agent which answers the questions based on the provided context"
        messages = [{'role':'system','content':system_guideline}]
        messages.append(messages_history)
        messages.append(new_messages)

        client = InferenceClient(model="openai/gpt-oss-20b" , token="hf_Gd3Gg0o75RfKG3IplnjVKC2tJulngVtKf5") 
        return client.chat_completion(messages=messages)
    


class TrueFalseModel(BaseModel):
    result : bool



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
                    "schema": TrueFalseModel.model_json_schema()
                }
            }
    )
        return TrueFalseModel.model_validate_json(completion.choices[0].message.content).result

    def related_question_detector(self,content,relavance_contents):
        system_prompt = f"You are a detector, you job is check a content and if it is related to this topic: \n{relavance_contents}\n you will return True, if not you will return False"
        return self.setUp_detector(system_prompt, content)

    def enough_context_to_answer_detector(self,content,relavance_contents):
        system_prompt = f"You are a detector, this information is provided for you: \n{relavance_contents}\n , user will ask you a question, your job is detecting if having this information can you answer to the question or no, if you can you will return True, if not you will return False"
        return self.setUp_detector(system_prompt, content)
