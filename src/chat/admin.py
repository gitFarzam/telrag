from django.contrib import admin
from .models import UserMessage, Conversation , TelegramMessage , Document , Chunk, Embedding


admin.site.register(Conversation)
admin.site.register(UserMessage)
admin.site.register(TelegramMessage)
admin.site.register(Document)
admin.site.register(Chunk)
admin.site.register(Embedding)
