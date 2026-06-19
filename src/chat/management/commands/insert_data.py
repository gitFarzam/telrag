from django.core.management.base import BaseCommand, CommandError
from django.conf import settings
from chat.services import intial_data_db_insert
import os
import chat.constants as constants
from chat.utils.utils import TerminalColor

class Command(BaseCommand):

    help = f"""
    Running command: python manage.py insert_data
    """

    def handle(self,*args,**options):
        color = TerminalColor()
        error_message = self.style.ERROR(f"Error!")
        success_message = self.style.SUCCESS(f"Done!!!")
        try:
            data_dir = os.path.join(settings.BASE_DIR,constants.data_path("telmart","initial"))
            
            number_of_docs, embeddings = intial_data_db_insert(data_dir)
            if number_of_docs > 0:
                self.stdout.write(self.style.NOTICE(f"{str(number_of_docs)} initial documents were added into database."))
                success = True

        except TypeError as e:
            success = False
            print(f"The documents you try to insert is already in the database, You can not have duplicated documents in the database, use {color.yellow("make del_data")} to delete initial data first")

        except Exception as e:
            success = False
            raise CommandError(f"Error: {e}")

        if success:
            self.stdout.write(success_message)
        else:
            self.stdout.write(error_message)