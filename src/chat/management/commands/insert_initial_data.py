from django.core.management.base import BaseCommand, CommandError
from chat.models import Conversation
from django.db import transaction
from django.conf import settings
from chat.services import creating_text_content_object, creating_document_source,creating_document_object,creating_chunk_objects,creating_embedding_objects,intial_data_db_insert,load_initial_documents
import os
from pathlib import Path
import chat.constants as constants

class Command(BaseCommand):

    help = f"""
    Running command: uv run manage.py insert_data <document_indices>
    Check initial_data directory, each text document is related to 1 sample
    In case you need to store documents for a beauty shop simply run this command:
    Running command: uv run manage.py insert_data 0 1 2 3
    (this inserts all documents from all indices, not that you should add a white space for each argument)
    """

    def handle(self,*args,**options):
        try:
            data_dir = os.path.join(settings.BASE_DIR,constants.data_path("telmart")["initial"])
            
            intial_data_db_insert(data_dir)

        except Exception as e:
            raise CommandError(f"Error: {e}")

        self.stdout.write(
            self.style.SUCCESS(f"Done!!!")
        )

        # python manage.py insert_initial_data