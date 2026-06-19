from django.core.management.base import BaseCommand
from chat.models import Document,DocumentSource


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