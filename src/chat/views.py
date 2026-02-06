from django.shortcuts import render, redirect
from .models import Conversation, UserMessage, TelegramMessage
from django.views.generic import DetailView, UpdateView,TemplateView
from core.models import User
from django.http import HttpResponse
from asgiref.sync import async_to_sync
from channels.layers import get_channel_layer
import uuid
from django.contrib.auth import authenticate,login
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
import json
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from .services import message_sender, process_telegram_message

class HomeView(TemplateView):
    template_name = 'home.html'


class NewConversationView(TemplateView):
    def post(self, request, *args, **kwargs):
        name = self.request.POST.get('name')
        if name:
            username = f"{uuid.uuid4()}"
            user = User(username=username)
            user.set_unusable_password()
            user.first_name = name
            user.save()

            login(self.request, user, backend="django.contrib.auth.backends.ModelBackend")
            
            conversation = Conversation.objects.create(user=user)
            return redirect('chat-detail', pk=conversation.pk)
        
        return HttpResponse("Name is required", status=400)


# Create your views here.
class ChatView(LoginRequiredMixin , UserPassesTestMixin , DetailView):
    model = Conversation
    template_name = 'chat.html'
    context_object_name = "conversation"

    # this function ensures that only the owner of the conversation can access it (using UserPassesTestMixin)
    def test_func(self):
        conversation = self.get_object()

        # admins can access any conversation
        if self.request.user.is_staff:
            return True
        return conversation.user == self.request.user

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["messages"] = self.object.messages.all().order_by("created_at")
        return context
        

    
class ChatSendMessageView(UpdateView):
    model = Conversation
    fields = []  # we are not editing Conversation fields

    def form_valid(self, form):
        conversation = self.get_object()
        content = self.request.POST.get("content")

        if content:
            message_sender(conversation,content,False)
            return HttpResponse(status=204)

        return HttpResponse("")
    



@csrf_exempt
def telegram_webhook(request):
    # print(request)
    tg_object = TelegramMessage.objects.create(transaction_type=True) # True means receving (False is for sending)
    tg_object.json_content = json.loads(request.body)
    tg_object.save()

    # process_live_agent_message(data)
    # print(data)
    # message = data.get("message")
    # if message:
    #     chat_id = message["chat"]["id"]
    #     text = message.get("text")

    #     print(f"Received message: {text} from chat: {chat_id}")

    #     if text:
    #         message_sender(Conversation.objects.get(pk=4),text,True)
    #         message =UserMessage.objects.create(
    #             conversation=Conversation.objects.get(pk=4),
    #             content=text,
    #             is_agent=True
    #         )

    return JsonResponse({"ok": True})
