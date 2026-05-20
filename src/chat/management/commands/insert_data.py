from django.core.management.base import BaseCommand, CommandError
from chat.models import Document
from django.db import transaction
from django.conf import settings
from chat.services import creating_text_content_object, creating_document_source,creating_document_object,creating_chunk_objects,creating_embedding_objects
import os
from pathlib import Path


class Command(BaseCommand):

    help = f"""
    Running command: uv run manage.py insert_data <document_indices>
    Check initial_data directory, each text document is related to 1 sample
    In case you need to store documents for a beauty shop simply run this command:
    Running command: uv run manage.py insert_data 0 1 2 3
    (this inserts all documents from all indices, not that you should add a white space for each argument)
    """

    def add_arguments(self,parser):
        parser.add_argument("root_name" , nargs="+" ,type=int)

    def load_documents(self,root_name="telburger"):
        """
        this function returns a dictionary which have category name as a key and file path as value, for example:

        {'crm_refund' : 'chat/management/commands/initial_data/telburger/crm/refund.txt',
        'general_general' : 'chat/management/commands/initial_data/telburger/general/general.txt',
        ...,
        } 
        """
        txt_files_dict = {}
        root_dir = os.path.join(settings.BASE_DIR,f'chat/management/commands/initial_data/{root_name}')
        dirs = os.listdir(root_dir)
        for dir in dirs:
            txt_file_path = os.path.join(root_dir,dir)
            txt_file = os.listdir(txt_file_path)
            txt_files_dict[f"{dir}_{Path(txt_file).stem}"] = txt_file_path
        return txt_files_dict


    def handle(self,*args,**options):
        root_name = options["root_name"]
        txt_files_dict = self.load_documents(root_name)
        for category in txt_files_dict:
            try:
                file_path = txt_files_dict[category]
                with open(file_path) as text_file:
                    text_string = text_file.read()
                    print(text_string)
                with transaction.atomic():
                    text_content_object = creating_text_content_object(content=text_string)
                    doc_source_object = creating_document_source(model_object=text_content_object)
                    doc_object = creating_document_object(document_source=doc_source_object,category=category , is_initial=True)
                    chunk_objects = creating_chunk_objects(document_object=doc_object)
                    embedding_objects = creating_embedding_objects(chunks=chunk_objects)

                    print(f"Embedding has been created: {embedding_objects}")

            except FileNotFoundError as e:
                raise CommandError('File %s.txt does not exist' % root_name)

        self.stdout.write(
            self.style.SUCCESS(f"Root: {root_name}")
        )

        # uv run manage.py insert_data 0