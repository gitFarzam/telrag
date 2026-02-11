from django.db import models
from pgvector.django import VectorField
import json
from django.conf import settings

class Conversation(models.Model):
    created_at = models.DateTimeField(auto_now_add=True)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    def __str__(self):
        return self.pk.__str__() + " - " + self.created_at.__str__()
    
class MessageGroup(models.Model):
    created_at = models.DateTimeField(auto_now_add=True)


class UserMessage(models.Model):
    content = models.CharField(max_length=20000)
    created_at = models.DateTimeField(auto_now_add=True)
    conversation = models.ForeignKey(Conversation, on_delete=models.CASCADE,related_name='messages')
    message_group = models.ForeignKey(MessageGroup , on_delete=models.CASCADE)
    tg_id = models.PositiveIntegerField(null=True,blank=True)

    def __str__(self):
        return self.content[:50]

class AgenMessage(models.Model):
    content = models.CharField(max_length=20000)
    created_at = models.DateTimeField(auto_now_add=True)
    conversation = models.ForeignKey(Conversation, on_delete=models.CASCADE,related_name='agent_messages')

    def __str__(self):
        return self.content[:50]

class TelegramMessage(models.Model):
    transaction_type = models.BooleanField(default=False) # Send -> False , Receive -> True
    json_content = models.JSONField()

    def data(self):
        return json.loads(self.json_content)


class Document(models.Model):
    CONTENT_TYPE_CHOICES = [
        ('photo','Photo'), ('audio', 'Audio') , ('text','Text') , ('video','Video')
    ]
    FILE_TYPE_CHOICES = [
        ('pdf','PDF') , ('jpg','JPG') , ('png','PNG') , ('gif','GIF') , ('txt','TXT')
    ]
    name = models.CharField(null=True,blank=True)
    format = models.CharField(choices=FILE_TYPE_CHOICES,default='txt')
    text = models.TextField(null=True,blank=True)
    file = models.FileField(null=True,blank=True)
    caption = models.TextField(null=True , blank=True)
    telegram_message = models.ForeignKey(TelegramMessage , on_delete=models.CASCADE)
    user_message = models.ForeignKey(UserMessage , on_delete=models.PROTECT , null=True , blank=True)
    
    def __str__(self):
        return self.name

class Chunk(models.Model):
    chunk_id = models.PositiveSmallIntegerField()
    overlap = models.PositiveIntegerField(default=0)
    text = models.TextField()
    document = models.ForeignKey(to=Document,on_delete=models.CASCADE)


class Embedding(models.Model):
    chunk = models.ForeignKey(to=Chunk , on_delete=models.CASCADE)
    vector = VectorField(dimensions=384)
