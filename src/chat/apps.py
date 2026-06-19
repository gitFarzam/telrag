<<<<<<< HEAD
from django.apps import AppConfig

class ChatConfig(AppConfig):
    name = 'chat'
    def ready(self):
        import chat.signals
||||||| 6d2c1b6
=======
from django.apps import AppConfig

class ChatConfig(AppConfig):
    name = 'chat'
>>>>>>> demo
