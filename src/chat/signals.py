from django.db.models.signals import post_save
from django.dispatch import receiver
from .models import UserMessage, TelegramMessage, Document
from .services import process_user_message, process_telegram_message, process_document_object

@receiver(post_save, sender=UserMessage)
def new_user_message_signal(sender, instance, created, **kwargs):
	if created:
		process_user_message(instance)

@receiver(post_save, sender=TelegramMessage)
def telegram_message_signal(sender, instance, created, **kwargs):
	if created:
		process_telegram_message(instance)

@receiver(post_save, sender=Document)
def document_parsing_signal(sender, instance, created, **kwargs):
	if created:
		process_document_object(instance)

# Source - https://stackoverflow.com/a/18532655
# Posted by Germano, modified by community. See post 'Timeline' for change history
# Retrieved 2026-02-09, License - CC BY-SA 3.0


