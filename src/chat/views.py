from django.shortcuts import render, redirect
from .models import Conversation,TelegramMessage
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
from .services import message_sender,ingestion_process,process_user_message,regex_for_get_verification_code,add_initial_documents
from .operations import telegram_message_processor
from django.conf import settings
import hmac
from .utils.telegram import send_message
from django.db import transaction
import time

# First edit in demo branch

# class HomeView(TemplateView):
#     def get(self, request, *args, **kwargs):
#         user = request.user
#         conversations = Conversation.objects.filter(user=user)
#         print(conversations)
#         print(f"User is {request.user}")
#         return render(request=request,template_name='home.html')

#     template_name='home.html'


class NewConversationView(TemplateView):

    def get(self, request, *args, **kwargs):
        user = request.user
        conversations = Conversation.objects.filter(user=user)
        print(conversations)
        print(f"User is {request.user}")
        return render(request=request,template_name='home.html')
    
    def post(self, request, *args, **kwargs):
        user = self.request.user
        name = self.request.POST.get('name')
        if name:
            # Check if the current user is authenticated  (logged in) , if yes , it shouldnt be able to create a new chat, or previous conversation should be deleted.

            if not user.is_authenticated:
                username = f"{uuid.uuid4()}"
                user = User(username=username)
                user.set_unusable_password()
                user.first_name = name
                user.save()

                print(f"User is (From Post) {user}")

                login(self.request, user, backend="django.contrib.auth.backends.ModelBackend")
                
                try:
                    conversation = Conversation.objects.create(user=user)
                    result = add_initial_documents(conversation=conversation)
                    if not result:
                        print("Couldnt add initial document")

                    return redirect('chat-detail', pk=conversation.pk)
                except ValueError as e:
                    print(f"Database error in creation conversation or/and chat id object, error: {e}")

            # if user is already authenticated return user to the current conversation
            conversation = Conversation.objects.filter(user=user).last()
            if conversation:
                return redirect('chat-detail', pk=conversation.pk)
            else:
                conversation = Conversation.objects.create(user=user)
                conversation.refresh_from_db()
                conversation.save()
                result = add_initial_documents(conversation=conversation)
                if not result:
                    print("Couldnt add initial document")

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
        # context["delete"] = self.get_object().delete()
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


    print(telegram_webhook.__name__)

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
        # print(f"**********\n{data}\n*************")
    except json.JSONDecodeError:
        return JsonResponse(
            {"error": "Invalid JSON"},
            status=200
        )

    if "message" not in data:
        print(f"message key is not detected in the json body! keys are: {data.keys()}")
        if "callback_query" not in data:
            print('->>>>>> Yes there is callback_query')
            return JsonResponse(
                {"error": "Missing required key: message"},
                status=200
            )
    
    # 2) Restrict which Telegram users can use the bot (e.g. admins only)
    
    # allowed_ids = settings.TELEGRAM_ALLOWED_USER_IDS 
    # allowed_ids += list(Conversation.objects.exclude(chat_id__isnull=True).values_list('chat_id', flat=True))
    
    # if allowed_ids:
    from_id = data.get("message", {}).get("from", {}).get("id")
    if from_id is None:
        from_id = data.get("callback_query", {}).get("from", {}).get("id")
    print(f'From ID: {from_id}')

    conversation = Conversation.objects.filter(chat_id=from_id).last()

    if not conversation:
        print("-> Regex for detecting verificatin code")
        regex_for_get_verification_code(data,from_id)
        return JsonResponse({"result": "ok"},status=200)
    else:
        print("Nope! You can pass!")

    
    last_message = TelegramMessage.objects.filter(chat_id=from_id).last()
    if last_message:
        last_time = last_message.created_at.timestamp()
        now_time = time.time()
        if now_time - last_time < 3:
            send_message(chat_id=last_message.chat_id,text="Your message has been rejected, please send it again 3 seconds later..")
            return JsonResponse({"result": "ok"},status=200)

    try: 
        data = json.loads(request.body.decode("utf-8"))
        telegram_message_processor(transaction_type=True , json_content = data)
        return JsonResponse({"result": "ok"},status=200)

    except Exception as e:
            print(f'Error: {e}')
            return JsonResponse({"result": 'ok'} , status=200)