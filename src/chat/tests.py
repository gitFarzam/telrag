from django.test import TestCase
from .models import TelegramMessage, Document, Chunk
import json
from http import HTTPStatus
import os
from django.conf import settings
from .services import process_telegram_object, process_document_object, proccess_chunk_objects
from .utils.rag import RAGToolKit
from unittest.mock import patch

class TestWebhook(TestCase):

    @patch('chat.views.ingestion_process', return_value=True)
    def test_if_webhook_returns_true(self ,mock_ingestion):
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

    def test_processing_telegram_message(self):
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
        return super().setUp()

    # Test if the embedder works correctly
    def test_embedding_function(self):
        ragtoolkit_instance = RAGToolKit()
        result = ragtoolkit_instance.embedder(chunks=["Hello How Are You?"])
        self.assertEqual(len(result[0]), 384)




 