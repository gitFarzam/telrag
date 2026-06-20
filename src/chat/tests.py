from django.test import TestCase
from django.conf import settings
from django.db.models import QuerySet
from .models import TelegramMessage, Document, Embedding
import json
from http import HTTPStatus
import os
from django.conf import settings
from .services import process_telegram_object,hybrid_search,intial_data_db_insert,load_initial_documents
from .utils.rag import LLM,audio_to_text,embedder,embedder
from .utils.telegram import telegram_downloader
from unittest.mock import patch
import chat.constants as constants
import pandas as pd
from dotenv import load_dotenv
from openai.types.chat import ChatCompletion
from openai.types.responses.response import Response
from chat.utils.utils import Utils,Markdown

load_dotenv()

class TestWebhook(TestCase):

    @patch('chat.services.ingestion_process', return_value=True)
    def test_if_webhook_returns_true(self , mock_ingestion):
        # Arrange
        file_relative_dir = "chat/test_data/telegram_text.json"
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

        file_relative_dir = "chat/test_data/telegram_text.json"
        file_dir = os.path.join(settings.BASE_DIR , file_relative_dir)

        with open(file_dir, "r", encoding="utf-8") as f:
            json_dict = json.loads(f.read())

        self.tg_object = TelegramMessage.objects.create(transaction_type=True , json_content = json_dict)

    def test_processing_text_telegram_message(self):
        result = process_telegram_object(self.tg_object)

        # if the output is a document instance or not
        self.assertIsInstance(result,Document)


class TestEmbedding(TestCase):

    # Test if the embedder works correctly
    def test_embedding_function(self):
        result = embedder(model=constants.HF_EMBEDDING_MODEL,text=["Hello How Are You?"])
        self.assertEqual(len(result[0]), 384)


class TestAudioTranscriber(TestCase):

    def setUp(self):
        # Creating telegram object
        audio_file_relative_dir = "chat/test_data/sample.oga"
        self.audio_file_dir = os.path.join(settings.BASE_DIR , audio_file_relative_dir)

    def audio_transcriber(self):
        result = audio_to_text(file_path=self.audio_file_dir,model=constants.OPENAI_TRANSCRIPTION_MODEL)
        self.assertIsInstance(result,str)



class TestTelegramFileDownload(TestCase):
    def setUp(self):
        self.voice_data = {'metadata': {'message_id': 156}, 'data': {'voice': {'duration': 14, 'mime_type': 'audio/ogg', 'file_id': 'AwACAgQAAxkBAAOdaZdP1djkwwcaUVeL1uCDW47FPAMAAmQfAAKYurlQLte1tVjyxvI6BA', 'file_unique_id': 'AgADZB8AApi6uVA', 'file_size': 57264}}}

    def test_downloading_file(self):
        result = telegram_downloader(self.voice_data['data']['voice']['file_id'])

        self.assertTrue(result,"An output for the file is existed")


class TestLLM(TestCase):
    def setUp(self):
        self.llm = LLM(
            model=constants.OPENAI_CHAT_MODEL,
        )
    def test_text_summarization(self):
        result = self.llm.openai_classifier(
            content="my name is Farzam",
            job='keyword_extraction'
        )
        self.assertIsInstance(result,ChatCompletion)
        self.assertGreaterEqual(result.choices[0].message.content.__len__(),1)

    def test_openai_text_genrator(self):
        
        messages_history = [
            {"role" : "assistant" , "content" : "Hi! this is TelMart! How can I help you?"},
            {"role" : "user" , "content" : "Hey! Do you know where can I find some good deals for groccery?"},
            {"role" : "assistant" , "content" : "Yes! You can check Telmart website to find good groccery deals!"}
        ]

        new_messages = {"role" : "user" , "content" : "But I couldn't find that!"}
        
        result = self.llm.openai_text_generator(messages_history,new_messages)

        self.assertIsInstance(result,ChatCompletion)
        self.assertGreaterEqual(result.choices[0].message.content.__len__(),1)

    def test_text_rewriter(self):
        original_text = "Yesterday, I went to your pharmacy and was unhappy with the behavior of your staff. One of your employees shouted at me, which is unacceptable."
        result = self.llm.openai_text_rewriter(original_text)

        self.assertIsInstance(result,Response)
        self.assertIsNotNone(result.output_text)


class TestInsertData(TestCase):
    def setUp(self):
        self.data_dir = constants.data_path("telmart","initial")
        self.abs_data_dir = os.path.join(settings.BASE_DIR,self.data_dir)

    def test_load_initial_documents(self):
        categories = os.listdir(self.abs_data_dir)
        result = load_initial_documents(self.abs_data_dir)
        self.assertEqual(result.__len__() , categories.__len__() , msg=f"The number of folders in the {self.abs_data_dir} path is equal to number of keys in categories dictionary and equals to {result.__len__()}")

    def test_intial_data_db_insert(self):
        number_of_docs, result = intial_data_db_insert(self.data_dir)
        self.assertGreaterEqual(result.__len__(),1,msg="Emebddings list at least have 1 value")
        [self.assertIsInstance(obj,Embedding,msg="Object class is Embedding") for obj in result]


class TestJsonlReader(TestCase):
    def setUp(self):
        self.jsonl_path = os.path.join(settings.BASE_DIR,constants.data_path("telmart","test_retrieval_question"))
        self.utils = Utils()
        
    def test_jsonl_reader(self):
        result = self.utils.jsonl_reader(path=self.jsonl_path)
        assert isinstance(result, pd.DataFrame)


class TestValueChecker(TestCase):
    def setUp(self):
        jsonl_path = os.path.join(settings.BASE_DIR,constants.data_path("telmart","test_retrieval_question"))
        self.test_raw_source = os.path.join(settings.BASE_DIR,constants.data_path("telmart","test_raw"))
        self.utils = Utils()
        self.df = self.utils.jsonl_reader(path=jsonl_path)

    def test_value_checker(self):
        result = self.utils.value_checker(self.df,self.test_raw_source)
        self.assertTrue(result)


class TestHybridSearch(TestCase):

    def setUp(self):
        self.search_keyword = "telmart"
        input_text = f"what does {constants.BUSINESS_NAME} do?"
        self.input_text_embedding = embedder(
            model=constants.HF_EMBEDDING_MODEL,
            text=[input_text]
            )[0]

        self.k = 5
    
    def test_hybrid_search(self):
        result = hybrid_search(
            self.search_keyword,
            self.input_text_embedding,
            self.k,
            beta=0
        )

        self.assertIsInstance(result,QuerySet)
