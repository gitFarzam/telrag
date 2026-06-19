<<<<<<< HEAD
from django.contrib import admin
from .models import Message, Conversation , TelegramMessage , Document , Chunk, Embedding,TelegramChatID


admin.site.register(Conversation)
admin.site.register(Message)
admin.site.register(TelegramMessage)
admin.site.register(Document)
admin.site.register(Chunk)
admin.site.register(Embedding)
admin.site.register(TelegramChatID)
||||||| 6d2c1b6
=======
from django.contrib import admin
from .models import Message, Conversation , TelegramMessage , Document , Chunk, Embedding


admin.site.register(Conversation)
admin.site.register(Message)
admin.site.register(TelegramMessage)
admin.site.register(Document)
admin.site.register(Chunk)
admin.site.register(Embedding)
>>>>>>> demo
