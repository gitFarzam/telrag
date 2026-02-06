from django.db import models
from pgvector.django import VectorField
from chat.models import TelegramMessage


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
    # telegram_message = models.ForeignKey(TelegramMessage , on_delete=models.CASCADE)
    


    def __str__(self):
        return self.name

class Chunk(models.Model):
    chunk_id = models.PositiveSmallIntegerField()
    overlap = models.PositiveIntegerField(default=0)
    text = models.TextField()
    # document = models.ForeignKey(to=Document,on_delete=models.CASCADE)


class Embedding(models.Model):
    chunk = models.ForeignKey(to=Chunk , on_delete=models.CASCADE)
    embedding = VectorField(dimensions=3)
