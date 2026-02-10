from django.contrib import admin
from .models import UserMessage, Conversation , TelegramMessage , Document

admin.site.register(Document)
admin.site.register(Conversation)
admin.site.register(UserMessage)
admin.site.register(TelegramMessage)
