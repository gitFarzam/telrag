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
        print(embedding)