from .models import Conversation
from channels.generic.websocket import WebsocketConsumer
from asgiref.sync import async_to_sync
from django.db.models import ProtectedError
from .services import message_sender_custom
class ChatConsumer(WebsocketConsumer):
    def connect(self):
        self.user = self.scope["user"]
        self.conversation_id = self.scope["url_route"]["kwargs"]["conversation_id"]
        self.group_name = f"chatgroup_{self.conversation_id}"

        async_to_sync(self.channel_layer.group_add)(
            self.group_name,
            self.channel_name,
        )
        
        self.accept()

    def disconnect(self, close_code):
        async_to_sync(self.channel_layer.group_discard)(
            self.group_name,
            self.channel_name,
        )

        
        # try:
        #     conversation_obj = Conversation.objects.filter(pk=int(self.conversation_id)).first()
        #     if conversation_obj:
        #         message_sender_custom(conversation_obj,message="This conversation is being deleted due to inactivity..")
        #         print(f"❌ Deleting conversation object: {conversation_obj} ❌")
        #         conversation_obj.delete()
        #     print("There is no conversation object...")
        # except ValueError as e:
        #     print(e)


    def message_handler(self, event):
        # Send raw HTML for htmx OOB swap (id + hx-swap-oob="beforeend")
        self.send(text_data=event["html_response"])