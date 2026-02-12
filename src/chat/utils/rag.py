from langchain_text_splitters import RecursiveCharacterTextSplitter
from typing import List
from langchain_core.documents.base import Document
from huggingface_hub import InferenceClient

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
    

class TextClassifier():
    def __init__(self,model="distilbert/distilbert-base-uncased-finetuned-sst-2-english", token="hf_Gd3Gg0o75RfKG3IplnjVKC2tJulngVtKf5"):

        client = InferenceClient(model=model,token=token)
        self.classifier = client.text_classification
        return super().__init__()
        
    def greeting_classifier(self,text):
        prompted_text = f"This sentence is about greeting: {text}"
        return self.classifier(text=prompted_text)
    
    def relevance_classifier(self,text,topics):
        prompted_text = f"{text} is related to: {topics}"
        return self.classifier(text=prompted_text)
    
    def rag_pipeline():
        level_1 = ['greeting' , 'request']
        level_2 = ['related',]
