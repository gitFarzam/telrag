from django.test import TestCase
from django.conf import settings
from django.db.models import QuerySet
from .models import TelegramMessage, Document, Chunk, Conversation, Embedding
from core.models import User
import json
from http import HTTPStatus
import os
from django.conf import settings
from .services import process_telegram_object,hybrid_search,intial_data_db_insert,load_initial_documents
from .utils.rag import NLP, RagMetrics
from .utils.telegram import telegram_downloader
from unittest.mock import patch
import chat.constants as constants
import pandas as pd

class TestWebhook(TestCase):

    @patch('chat.views.ingestion_process', return_value=True)
    def test_if_webhook_returns_true(self , mock_ingestion):
        # Arrange
        file_relative_dir = "chat/sample_data/telegram_text.json"
        file_dir = os.path.join(settings.BASE_DIR , file_relative_dir)

        with open(file_dir, "r", encoding="utf-8") as f:
            json_text = f.read()

        # Act
        response = self.client.post(
            "/webhook/",
            data=json_text,
            content_type="application/json"
        )

        # Assert
        self.assertEqual(response.status_code,HTTPStatus.OK)



class TestTelegramMessageParsing(TestCase):

    # Arrange
    def setUp(self):

        file_relative_dir = "chat/sample_data/telegram_text.json"
        file_dir = os.path.join(settings.BASE_DIR , file_relative_dir)

        with open(file_dir, "r", encoding="utf-8") as f:
            json_text = f.read()

        self.tg_object = TelegramMessage.objects.create(transaction_type=True , json_content = json_text)
        print("Fake telegram object has been created")

    def test_processing_text_telegram_message(self):
        result = process_telegram_object(self.tg_object)

        # if the output is a document instance or not
        self.assertIsInstance(result,Document)


class TestDocumentIngestion(TestCase):

    def setUp(self):

        # Creating telegram object
        json_file_relative_dir = "chat/sample_data/telegram_text.json"
        json_file_dir = os.path.join(settings.BASE_DIR , json_file_relative_dir)

        with open(json_file_dir, "r", encoding="utf-8") as f:
            json_text = f.read()

        tg_object = TelegramMessage.objects.create(transaction_type=True , json_content = json_text)

        # Creating document object
        text_file_relative_dir = "chat/sample_data/text_context.txt"
        text_file_dir = os.path.join(settings.BASE_DIR , text_file_relative_dir)

        with open(text_file_dir, "r", encoding="utf-8") as f:
            text = f.read()

        self.doc_object = Document.objects.create(telegram_message=tg_object,text=text)

        chunk_1 = Chunk.objects.create(chunk_id=1,text="This part is for chunk 1", document=self.doc_object)
        chunk_2 = Chunk.objects.create(chunk_id=2,text="This part is for chunk 2", document=self.doc_object)

        self.chunks = [chunk_1, chunk_2]

    def test_processing_document(self):
        result = process_document_object(self.doc_object)
        self.assertIsInstance(result, list)


    # test if the process of converting chunks to embedding works correctly
    def test_proccess_chunks(self):
        result = proccess_chunk_objects(chunks=self.chunks)
        print(result)
        self.assertIsInstance(result,list)



class TestRAGToolKit(TestCase):

    def setUp(self):
        # Creating telegram object
        audio_file_relative_dir = "chat/sample_data/sample.oga"
        self.audio_file_dir = os.path.join(settings.BASE_DIR , audio_file_relative_dir)

        self.rt = RAGToolKit()

    # Test if the embedder works correctly
    def test_embedding_function(self):
        result = self.rt.embedder(chunks=["Hello How Are You?"])
        self.assertEqual(len(result[0]), 384)

    def test_text_generator_function(self):
        result = self.rt.text_generator(messages=[{'role':'user','content':'Talk about Iran'}])
        print(result)

    def audio_transcriber(self):
        result = self.rt.audio_to_text(file_path=self.audio_file_dir)
        print(result)


class TestTextClassifier(TestCase):

    def test_greeting_text_classifier_function(self):
        classifier_instance = RetirievalNavigator(model="distilbert/distilbert-base-uncased-finetuned-sst-2-english", token="hf_Gd3Gg0o75RfKG3IplnjVKC2tJulngVtKf5")
        result = classifier_instance.greeting_classifier(text="Hi I have a question")
        print(result)

    def test_related_question_detector(self):

        completion_instance = RetirievalNavigator(model="meta-llama/Llama-3.1-8B-Instruct", token="hf_Gd3Gg0o75RfKG3IplnjVKC2tJulngVtKf5")

        topics_file_dir_relative = "chat/sample_data/company.txt"
        topics_file_dir = os.path.join(settings.BASE_DIR , topics_file_dir_relative)
        with open(topics_file_dir,'r') as f:
            topics = f.read()

        result = completion_instance.related_question_detector(content="Hey how are you" , relavance_contents=topics)

        print(result)


    def test_enough_context_to_answer_detector(self):

        completion_instance = RetirievalNavigator(model="meta-llama/Llama-3.1-8B-Instruct", token="hf_Gd3Gg0o75RfKG3IplnjVKC2tJulngVtKf5")

        relavance_contents = "you can return up to 6 month,we have refund"

        result = completion_instance.related_question_detector(content="What is you refund policy?" , relavance_contents=relavance_contents)

        print(result)


class TestTelegramFileDownload(TestCase):
    def setUp(self):
        self.voice_data = {'metadata': {'message_id': 156}, 'data': {'voice': {'duration': 14, 'mime_type': 'audio/ogg', 'file_id': 'AwACAgQAAxkBAAOdaZdP1djkwwcaUVeL1uCDW47FPAMAAmQfAAKYurlQLte1tVjyxvI6BA', 'file_unique_id': 'AgADZB8AApi6uVA', 'file_size': 57264}}}

    def test_downloading_file(self):
        result = telegram_downloader(self.voice_data['data']['voice']['file_id'])

        self.assertTrue(result,"An output for the file is existed")


class TestInsertData(TestCase):
    def setUp(self):
        self.data_dir = constants.data_path("telmart")["initial"]
        self.abs_data_dir = os.path.join(settings.BASE_DIR,self.data_dir)
    def test_load_initial_documents(self):
        categories = os.listdir(self.abs_data_dir)
        result = load_initial_documents(self.abs_data_dir)
        self.assertEqual(result.__len__() , categories.__len__() , msg=f"The number of folders in the {self.abs_data_dir} path is equal to number of keys in categories dictionary and equals to {result.__len__()}")

    def test_intial_data_db_insert(self):
        result = intial_data_db_insert(self.data_dir)
        self.assertGreaterEqual(result.__len__(),1,msg="Emebddings list at least have 1 value")
        [self.assertIsInstance(obj,Embedding,msg="Object class is Embedding") for obj in result]

class TestJsonlReader(TestCase):
    def setUp(self):
        self.jsonl_path = os.path.join(settings.BASE_DIR,constants.data_path("telmart")["test_retrieval_question_jsonl"])
        self.nlp = NLP()
        
    def test_jsonl_reader(self):
        result = self.nlp.jsonl_reader(path=self.jsonl_path)
        assert isinstance(result, pd.DataFrame)


class TestEmbedder(TestCase):
    def setUp(self):
        jsonl_path = os.path.join(settings.BASE_DIR,constants.data_path("telmart")["test_retrieval_question_jsonl"])
        self.nlp = NLP()
        self.df = self.nlp.jsonl_reader(path=jsonl_path)

    def test_embedder(self):
        embeddings = self.nlp.embedder(
            model=constants.HF_EMBEDDING_MODEL,
            chunks=self.df['query'].tolist()[:5]
            )
        self.assertEqual(len(embeddings), 5) # Checking the number of embeddings
        self.assertEqual(len(embeddings[0]), 384) # Checking the lenfth of each 


class TestValueChecker(TestCase):
    def setUp(self):
        jsonl_path = os.path.join(settings.BASE_DIR,constants.data_path("telmart")["test_retrieval_question_jsonl"])
        self.test_raw_source = os.path.join(settings.BASE_DIR,constants.data_path("telmart")["test_raw"])
        self.nlp = NLP()
        self.df = self.nlp.jsonl_reader(path=jsonl_path)

    def test_value_checker(self):
        result = self.nlp.value_checker(self.df,self.test_raw_source)
        self.assertTrue(result)

class TestHybridSearch(TestCase):

    def setUp(self):
        self.search_keyword = "telmart"

        input_text = "what does telmart do?"
        nlp = NLP()
        self.input_text_embedding = nlp.embedder(
            model=constants.HF_EMBEDDING_MODEL,
            chunks=[input_text]
            )[0]

        self.k = 5
        return super().setUp()
    
    def test_hybrid_search(self):
        result = hybrid_search(
            self.search_keyword,
            self.input_text_embedding,
            self.k
        )

        print(result)

        self.assertEqual(result.__len__(),self.k)