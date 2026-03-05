from django.db import models
from django.contrib.contenttypes.models import ContentType
from django.contrib.contenttypes.fields import GenericForeignKey
from pgvector.django import VectorField
import json
from django.conf import settings

class Conversation(models.Model):
    created_at = models.DateTimeField(auto_now_add=True)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    def __str__(self):
        return self.pk.__str__() + " - " + self.created_at.__str__()
    

class Message(models.Model):
    content = models.CharField(max_length=20000)
    created_at = models.DateTimeField(auto_now_add=True)
    conversation = models.ForeignKey(Conversation, on_delete=models.CASCADE,related_name='messages')
    is_agent = models.BooleanField(default=False)
    tg_id = models.PositiveIntegerField(null=True,blank=True)

    def __str__(self):
        return self.content[:50]


class TelegramMessage(models.Model):
    transaction_type = models.BooleanField(default=False) # Send -> False , Receive -> True
    json_content = models.JSONField()

    def data(self):
        return self.json_content


class DocumentSource(models.Model):
    content_type = models.ForeignKey(ContentType, on_delete=models.PROTECT)
    object_id = models.PositiveIntegerField()
    content_object = GenericForeignKey()


class TextContent(models.Model):
    content = models.TextField(null=True,blank=True)

class AudioContent(models.Model):
    file = models.FileField(upload_to='voices')
    trascription = models.TextField(null=True,blank=True)

class Document(models.Model):
    caption = models.TextField(null=True , blank=True)
    document_source = models.ForeignKey(DocumentSource , on_delete=models.CASCADE,null=True)
    user_message = models.ForeignKey(Message , on_delete=models.PROTECT , null=True , blank=True, related_name='documents')
    telegram_message = models.ForeignKey(TelegramMessage,on_delete=models.PROTECT,null=True)


class Chunk(models.Model):
    chunk_id = models.PositiveSmallIntegerField()
    overlap = models.PositiveIntegerField(default=0)
    text = models.TextField()
    document = models.ForeignKey(to=Document,on_delete=models.CASCADE)


class Embedding(models.Model):
    chunk = models.ForeignKey(to=Chunk , on_delete=models.CASCADE)
    vector = VectorField(dimensions=384)


class TelegramChatID(models.Model):
    chat_id = models.PositiveIntegerField(null=True,unique=True)
    conversation = models.OneToOneField(to=Conversation,on_delete=models.CASCADE)
    code = models.PositiveIntegerField(null=True)
    is_verified = models.BooleanField(default=False)
    is_active = models.BooleanField(default=False)
