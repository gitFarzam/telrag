from django.contrib import admin
from .models import UserMessage, Conversation

admin.site.register(Conversation)
admin.site.register(UserMessage)
