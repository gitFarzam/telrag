from django.db import models
import json
from django.conf import settings


class Conversation(models.Model):
    created_at = models.DateTimeField(auto_now_add=True)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    def __str__(self):
        return self.pk.__str__() + " - " + self.created_at.__str__()

class UserMessage(models.Model):
    content = models.CharField(max_length=20000)
    created_at = models.DateTimeField(auto_now_add=True)
    conversation = models.ForeignKey(Conversation, on_delete=models.CASCADE,related_name='messages')
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
