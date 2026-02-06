from django.db.models.signals import post_save
from django.dispatch import receiver
from .models import UserMessage, TelegramMessage
from .services import process_user_message, process_telegram_message

@receiver(post_save, sender=UserMessage)
def new_user_message_signal(sender, instance, created, **kwargs):
	if created:
		process_user_message(instance)

@receiver(post_save, sender=TelegramMessage)
def telegram_message_signal(sender, instance, created, **kwargs):
	if created:
		process_telegram_message(instance)