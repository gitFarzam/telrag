from django.core.management.base import BaseCommand, CommandError
from chat.models import Conversation,Document
from django.db import transaction
from django.conf import settings
from chat.services import creating_text_content_object, creating_document_source,creating_document_object,creating_chunk_objects,creating_embedding_objects
import os
from pathlib import Path


class Command(BaseCommand):

    help = f"""
    Deleting all initial data from database
    """


    def handle(self,*args,**options):
        Document.objects.all().exclude(category="user_input").delete()

        self.stdout.write(
            self.style.SUCCESS(f"All initial documents are deleted from database")
        )

        # python manage.py del_inital_data