from django.shortcuts import render, redirect
from .models import Conversation,TelegramChatID
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
from django.core.exceptions import ValidationError
from django.views.decorators.csrf import csrf_exempt
from .services import message_sender, process_telegram_object,ingestion_process,process_user_message
from django.conf import settings
import hmac
from .utils.telegram import send_message

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
            message_object = message_sender(conversation,content,False)
            process_user_message(message_object)
            return HttpResponse(status=204)

        return HttpResponse("")
    



@csrf_exempt
def telegram_webhook(request):

    if not request.body:
        error = "Request body is required"
        print(error)
        return JsonResponse(
            {"error": error},
            status=200
        )
        

    # 1) Verify request is from Telegram (rejects random POSTs to your webhook URL)
    secret = settings.TELEGRAM_WEBHOOK_SECRET
    if secret:
        token = request.headers.get("X-Telegram-Bot-Api-Secret-Token", "")
        if not hmac.compare_digest(secret, token):
            print("Request im webhook is not from telegram!")
            return JsonResponse({"error": "Forbidden"}, status=200)


    try:
        data = json.loads(request.body)
        print(data)
    except json.JSONDecodeError:
        return JsonResponse(
            {"error": "Invalid JSON"},
            status=200
        )

    if "message" not in data:
        return JsonResponse(
            {"error": "Missing required key: message"},
            status=200
        )
    

    # 2) Restrict which Telegram users can use the bot (e.g. admins only)
    chat_ids = list(TelegramChatID.objects.exclude(chat_id__isnull=True).values_list('chat_id', flat=True))
    allowed_ids = settings.TELEGRAM_ALLOWED_USER_IDS + chat_ids
    print('allowed_ids: ',allowed_ids)
    if allowed_ids:
        from_id = data.get("message", {}).get("from", {}).get("id")
        print(f'From ID: {from_id}')
        if from_id is None or from_id not in allowed_ids:
            import re

            text = data.get("message", {}).get("text", {})
            numbers = re.findall(r"\b[1-9]\d*\b", text)
            numbers = [int(n) for n in numbers]

            for number in numbers:
                if str(number) in data.get("message", {}).get("text", {}):
                    tg_chatid = TelegramChatID.objects.filter(code=number).first()
                    print(f"TG chat_id: {tg_chatid}")
                    if tg_chatid:
                        tg_chatid.chat_id = from_id
                        tg_chatid.is_verified = True
                        # also it should get conversation model from somewhere
                        tg_chatid.save()
                        send_message(chat_id=tg_chatid.chat_id,text="✅ verification code has been detected in your message, You are verified now")
                        return JsonResponse({"result": "ok"}, status=200)
                    else:
                        send_message(chat_id=from_id,text="Wrong code! Please check chat window and just send the code you are seeing on the window!")
            else:
                print('Access Denied!!!!')
                # it should be checked if user telegram account is verified or no
                return JsonResponse({"error": "Forbidden"}, status=200) # returning 200 is crucial, otherwise requests will repeadedly be send through webhook again and again!


    try:
        data = json.loads(request.body.decode("utf-8"))
        result = ingestion_process(transaction_type=True , json_content = data)
        return JsonResponse({"result": result},status=200)
    
    except Exception as e:
            print(f'Error in ingestion process: {e}')
            return JsonResponse({"result": 'ok'} , status=200)
        
