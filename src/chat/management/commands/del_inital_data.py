from django.core.management.base import BaseCommand, CommandError
from chat.models import Conversation,Document,DocumentSource,TextContent
from django.db import transaction
from django.conf import settings
from chat.services import creating_text_content_object, creating_document_source,creating_document_object,creating_chunk_objects,creating_embedding_objects
import os
from pathlib import Path
from django.contrib.contenttypes.models import ContentType

class Command(BaseCommand):

    help = f"""
    Deleting all initial data from database
    """


    def handle(self,*args,**options):

        documents = Document.objects.all().exclude(category="user_input")

        sources = DocumentSource.objects.filter(
            documents__in=documents
        ).distinct()

        # This still does not delete TextContent and AudioContent Related to them! better idea, adding both as fields to sources

        self.stdout.write(
            self.style.SUCCESS(f"All initial documents are deleted from database")
        )

        # python manage.py del_inital_data