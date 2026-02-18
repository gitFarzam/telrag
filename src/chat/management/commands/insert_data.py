from django.core.management.base import BaseCommand, CommandError
from chat.models import Document
from django.db import transaction
from django.conf import settings
from chat.services import creating_text_content_object, creating_document_source,creating_document_object,creating_chunk_objects,creating_embedding_objects
import os



class Command(BaseCommand):

    help = f"""
    Running command: uv run manage.py insert_data <document_indices>
    Check initial_data directory, each text document is related to 1 sample
    In case you need to store documents for a beauty shop simply run this command:
    Running command: uv run manage.py insert_data 0 1 2 3
    (this inserts all documents from all indices, not that you should add a white space for each argument)
    """

    def add_arguments(self,parser):
        parser.add_argument("document_indices" , nargs="+" ,type=int)

    def handle(self,*args,**options):
        document_indices = options["document_indices"]
        dir = os.path.join(settings.BASE_DIR,'chat/management/commands/initial_data')
        for document_index in document_indices:
            try:
                file_path = os.path.join(dir,f'{document_index}.txt')
                with open(file_path) as text_file:
                    text_string = text_file.read()
                    print(text_string)
                with transaction.atomic():
                    text_content_object = creating_text_content_object(content=text_string)
                    doc_source_object = creating_document_source(model_object=text_content_object)
                    doc_object = creating_document_object(document_source=doc_source_object)
                    chunk_objects = creating_chunk_objects(document_object=doc_object)
                    embedding_objects = creating_embedding_objects(chunks=chunk_objects)

                    print(f"Embedding has been created: {embedding_objects}")

            except FileNotFoundError as e:
                raise CommandError('File %s.txt does not exist' % document_index)

        self.stdout.write(
            self.style.SUCCESS(f"Document number: {document_indices}")
        )

        # uv run manage.py insert_data 0