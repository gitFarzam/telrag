from django.core.management.base import BaseCommand, CommandError
from django.conf import settings
from chat.services import intial_data_db_insert
import os
import chat.constants as constants

class Command(BaseCommand):

    help = f"""
    Running command: python manage.py insert_data
    """

    def handle(self,*args,**options):
        error_message = self.style.ERROR(f"Error!")
        success_message = self.style.SUCCESS(f"Done!!!")
        try:
            data_dir = os.path.join(settings.BASE_DIR,constants.data_path("telmart","initial"))
            
            success = intial_data_db_insert(data_dir)

        except Exception as e:
            success = False
            raise CommandError(f"Error: {e}")

        if success:
            self.stdout.write(success_message)
        else:
            self.stdout.write(error_message)

        # python manage.py insert_initial_data