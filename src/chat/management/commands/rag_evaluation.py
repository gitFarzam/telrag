from django.core.management.base import BaseCommand, CommandError
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
        precision = ragmetrics.precision(ret_test_data_path, top_k=10) # this should find the same document and not the same category (or maybe both)
        # hallucination = ragmetrics.llm_hallucination(llm_test_data_path,top_k=5)

        # except Exception as e:
        #     raise CommandError(f"Error: {e}")

        self.stdout.write(
            self.style.SUCCESS(f"Done!!!")
        )

        # python manage.py rag_evaluation