from django.db import models
from django.conf import settings


class Conversation(models.Model):
    created_at = models.DateTimeField(auto_now_add=True)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    def __str__(self):
        return self.pk.__str__() + " - " + self.created_at.__str__()

class Message(models.Model):
    content = models.CharField(max_length=20000)
    is_agent = models.BooleanField(default=False , editable=False)
    created_at = models.DateTimeField(auto_now_add=True)
    conversation = models.ForeignKey(Conversation, on_delete=models.CASCADE,related_name='messages')

    def __str__(self):
        return self.content[:50]