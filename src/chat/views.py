# Standard Library Imports
import os
import time
import logging
import hmac
import uuid
import json

# Django imports
from django.shortcuts import render, redirect, get_object_or_404
from django.http import HttpResponse,JsonResponse
from django.contrib.auth import login, logout
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.conf import settings
from django.views.decorators.csrf import csrf_exempt
from django.views import View
from django.views.generic import DetailView, UpdateView,TemplateView
from django.db import DatabaseError

# Local imports
from core.models import User
from .models import Conversation,TelegramMessage
from .services import message_sender,process_user_message,regex_for_get_verification_code,add_initial_documents
from .operations import telegram_message_processor
from .utils.telegram import send_message


# Creating an instance of the logging object
logger = logging.getLogger(__name__)


# Redirecting all not found pages to home page
def redirect_404(request, exception):
    return redirect('/')


# HomeView: Handling first page view and post view for creating a new conversation
class HomeView(TemplateView):
    def get(self, request, *args, **kwargs):
        return render(request=request,template_name='home.html')

    def post(self, request, *args, **kwargs):
        user = self.request.user
        name = self.request.POST.get('name')

        if not user.is_staff:
            logger.info("User is not staff")
            if name:
                # if the current user is authenticated  (logged in), should not be able to create a new chat, or previous conversation should be deleted.
                if not user.is_authenticated:
                    logger.info("User is not authenticated, Creating a new user")
                    username = f"{uuid.uuid4()}"
                    user = User(username=username)
                    user.set_unusable_password()
                    user.first_name = name
                    user.save()
                    logger.debug(f"{user.username} -  has been created")

                    logger.debug(f"{user.username} - loggin in")
                    login(self.request, user, backend="django.contrib.auth.backends.ModelBackend")
                    logger.debug(f"{user.username} - logged in")
                    
                    logger.info("Try: Creating  new conversation")
                    try:
                        conversation = Conversation.objects.create(user=user)
                        result = add_initial_documents(conversation=conversation)
                        
                        if result:
                            logger.info("Conversation has been created, redirecting to chat page...")
                            return redirect('chat-detail', pk=conversation.pk)
                        else:
                            logger.error("Error in adding initial data for user")
                            return render(request=request,template_name='home.html')
                    except DatabaseError:
                        logger.exception("Failed to create conversation object")


                # if user is already authenticated redirect user to the current conversation
                conversation = Conversation.objects.filter(user=user).last()
                if conversation:
                    return redirect('chat-detail', pk=conversation.pk)
                else:
                    conversation = Conversation.objects.create(user=user)
                    conversation.refresh_from_db()
                    conversation.save()

                    # I'm gonna delete this
                    # result = add_initial_documents(conversation=conversation)
                    # if not result:
                    #     logger.error("Error in adding initial data for user")
                    #     return render(request=request,template_name='home.html')
                    return redirect('chat-detail', pk=conversation.pk)
            
            return HttpResponse("Name is required", status=400)
        return HttpResponse("Logout from admin user", status=400)


class DeleteConversationUserView(LoginRequiredMixin, UserPassesTestMixin, View):
    def test_func(self):
        conversation = get_object_or_404(Conversation, pk=self.kwargs["pk"])
        if self.request.user.is_staff:
            return True
        return conversation.user == self.request.user

    def post(self, request, pk):
        conversation = get_object_or_404(Conversation, pk=pk)
        user = conversation.user
        if request.user == user:
            logout(request)
        user.delete()
        return redirect("home")


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
            logger.debug("Staff user login")
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
    print(telegram_webhook.__name__)
    if not request.body:
        error = "Request body is required"
        logger.info(error)
        return JsonResponse(
            {"error": error},
            status=200
        )
        
    # 1) Verify request is from Telegram (rejects random POSTs to your webhook URL)
    secret = settings.TELEGRAM_WEBHOOK_SECRET
    if settings.DEBUG:
        secret = settings.TELEGRAM_DEV_WEBHOOK_SECRET
    if secret:
        token = request.headers.get("X-Telegram-Bot-Api-Secret-Token", "")
        if not hmac.compare_digest(secret, token):
            logger.info("Request im webhook is not from telegram!")
            return JsonResponse({"error": "Forbidden"}, status=200)
        else:
            logger.info("Webhook secret has been detected")

    try:
        data = json.loads(request.body)
    except json.JSONDecodeError:
        logger.error("Invalid JSON from Telegram")
        return JsonResponse(
            {"error": "Invalid JSON"},
            status=200
        )

    if "message" not in data:
        logger.error(f"message key is not detected in the json body! keys are: {data.keys()}")
        if "callback_query" not in data:
            return JsonResponse(
                {"error": "Missing required key: message"},
                status=200
            )
    
    from_id = data.get("message", {}).get("from", {}).get("id")
    if from_id is None:
        from_id = data.get("callback_query", {}).get("from", {}).get("id")
    logger.info(f'Telegram message from ID: {from_id}')

    conversation = Conversation.objects.filter(chat_id=from_id).last()

    if not conversation:
        logger.info("Regex for detecting verificatin code")
        regex_for_get_verification_code(data,from_id)
        return JsonResponse({"result": "ok"},status=200)

    last_message = TelegramMessage.objects.filter(chat_id=from_id).last()
    if last_message:
        last_time = last_message.created_at.timestamp()
        now_time = time.time()
        if now_time - last_time < 3:
            send_message(chat_id=last_message.chat_id,text="Your message has been rejected, please send it again 3 seconds later..")
            return JsonResponse({"result": "ok"},status=200)

    try: 
        data = json.loads(request.body.decode("utf-8"))
        logger.info(f"Data file frem telegram webhook:\n{data}")
        telegram_message_processor(transaction_type=True , json_content = data)
        return JsonResponse({"result": "ok"},status=200)

    except Exception as e:
            logger.critical()
            return JsonResponse({"result": 'ok'} , status=200)