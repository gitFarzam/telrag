from django.core.management.base import BaseCommand, CommandError
from chat.models import Conversation
from django.db import transaction
from django.conf import settings
from chat.services import creating_text_content_object, creating_document_source,creating_document_object,creating_chunk_objects,creating_embedding_objects,intial_data_db_insert,load_initial_documents
import os
from pathlib import Path
import chat.constants as constants
from chat.utils.rag import RagMetrics

class Command(BaseCommand):

    help = f"""
    Evaluating RAG system
    """

    def handle(self,*args,**options):
        ret_test_data_path = constants.data_path('telmart')['test_retrieval_question_jsonl']
        llm_test_data_path = constants.data_path('telmart')['llm_eval_qa']
        ragmetrics = RagMetrics(model=constants.OPENAI_CHAT_MODEL,beta=constants.BETA)

        # try:
        # precision = ragmetrics.precision(ret_test_data_path, top_k=10)
        hallucination = ragmetrics.llm_hallucination(llm_test_data_path,top_k=5)

        # except Exception as e:
        #     raise CommandError(f"Error: {e}")

        self.stdout.write(
            self.style.SUCCESS(f"Done!!!")
        )

        # python manage.py rag_evaluation