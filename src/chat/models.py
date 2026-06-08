import json

from django.db import models
from django.contrib.contenttypes.models import ContentType
from django.contrib.contenttypes.fields import GenericForeignKey
from django.conf import settings

from django_prometheus.models import ExportModelOperationsMixin
from pgvector.django import VectorField

class Conversation(ExportModelOperationsMixin('conversation'), models.Model):
    created_at = models.DateTimeField(auto_now_add=True)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)

    chat_id = models.PositiveIntegerField(null=True,unique=True)
    code = models.PositiveIntegerField(null=True)
    is_verified = models.BooleanField(default=False)
    is_active = models.BooleanField(default=False)

    class Meta: 
        constraints = [
            models.UniqueConstraint(fields=["user"] , name="unique_user_per_conversation"),
            models.UniqueConstraint(fields=["chat_id"] , name="unique_chat_id_per_conversation")
        ]


    def __str__(self):
        return self.pk.__str__()
    

class RAGPipeline(models.Model):
    created_at = models.DateTimeField(auto_now_add=True)

class RagComponent(models.Model):
    ragpipeline=models.ForeignKey(RAGPipeline, on_delete=models.CASCADE)
    component_name = models.CharField()
    conversation = models.ForeignKey(Conversation , on_delete=models.SET_NULL , null=True)
    input_text = models.CharField(null=True)
    output_text = models.CharField(null=True)
    model = models.CharField(null=True)
    currency = models.CharField(null=True)
    embedding_cost = models.FloatField(null=True)
    input_cost = models.FloatField(null=True)
    output_cost = models.FloatField(null=True)
    latency = models.FloatField()

    

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
    created_at = models.DateTimeField(auto_now_add=True,null=True)
    chat_id = models.PositiveIntegerField(default=0)

    def data(self):
        return self.json_content


class DocumentSource(models.Model):
    content_type = models.ForeignKey(ContentType, on_delete=models.PROTECT)
    object_id = models.PositiveIntegerField()
    content_object = GenericForeignKey()


class TextContent(models.Model):
    file = models.FileField(upload_to="texts",null=True,blank=True)
    content = models.TextField(null=True,blank=True)


class AudioContent(models.Model):
    file = models.FileField(upload_to='voices')
    trascription = models.TextField(null=True,blank=True)


class Document(models.Model):
    conversation = models.ForeignKey(Conversation,on_delete=models.CASCADE,related_name="conv_documents",null=True,blank=True) 
    caption = models.TextField(null=True , blank=True)
    document_source = models.ForeignKey(DocumentSource , on_delete=models.CASCADE,null=True)
    user_message = models.ForeignKey(Message , on_delete=models.CASCADE , null=True , blank=True, related_name='documents')
    telegram_message = models.ForeignKey(TelegramMessage,on_delete=models.CASCADE,null=True)
    is_initial = models.BooleanField(default=False)
    category = models.CharField(null=True,blank=True,default="user_input")


class Chunk(models.Model):
    chunk_id = models.PositiveSmallIntegerField()
    overlap = models.PositiveIntegerField(default=0)
    text = models.TextField()
    document = models.ForeignKey(to=Document,on_delete=models.CASCADE)


class Embedding(models.Model):
    chunk = models.ForeignKey(to=Chunk , on_delete=models.CASCADE)
    vector = VectorField(dimensions=384)
