from django.test import TestCase
from .models import TelegramMessage, Document
import json
from http import HTTPStatus
import os
from django.conf import settings
from .services import process_telegram_message, process_document_object, proccess_chunks
from .utils.rag import RAGToolKit

# disabling telegram_message_signal signal temporary
from django.db.models.signals import post_save
from chat.signals import telegram_message_signal,document_parsing_signal

class TestWebhook(TestCase):

    def test_if_webhook_returns_200_response(self):
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
        process_telegram_message(self.tg_object)


class TestDocumentIngestion(TestCase):

    def setUp(self):
        # Disconnecting a singal which triggers when a TelegramMessage and Document object has been created
        post_save.disconnect(
            receiver=telegram_message_signal,
            sender=TelegramMessage,
        )

        post_save.disconnect(
            receiver=document_parsing_signal,
            sender=Document,
        )

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

    def test_processing_document(self):
        process_document_object(self.doc_object)


class TestRAGToolKit(TestCase):

    def test_embedding_function(self):
        ragtoolkit_instance = RAGToolKit()
        embedding = ragtoolkit_instance.embedder(chunks=["Hello How Are You?"])
        print(embedding)


    def test_proccess_chunks(self):
        proccess_chunks()

