# Standard libraries imports
import os
import logging
import hmac
import uuid
import json

# Django imports
from django.shortcuts import render, redirect
from django.http import HttpResponse,JsonResponse
from django.contrib.auth import login
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.conf import settings
from django.views.decorators.csrf import csrf_exempt
from django.views.generic import DetailView, UpdateView,TemplateView
from django.db import DatabaseError

# Local imports
from core.models import User
from .models import Conversation
from .services import message_sender,process_user_message
from .operations import telegram_message_processor
from chat.utils.redact import Redact

from dotenv import load_dotenv

# Loading virtual envs
load_dotenv()


# Creating an instance of the logging object
logger = logging.getLogger(__name__)
redact = Redact()


# Redirecting all 'Not Found' pages to the home page
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

                    logger.info(f"The user with username: {redact.redact_id(user.username)} -  has been created",extra={'user_id':user.pk})

                    login(self.request, user, backend="django.contrib.auth.backends.ModelBackend")

                    logger.debug(f"The user: {redact.redact_id(user.username)} - logged in",)
                    
                    logger.info("Try: Creating  new conversation")
                    try:
                        conversation = Conversation.objects.create(user=user)
                        if conversation:
                            logger.info("Conversation has been created, redirecting to chat page...",extra={'conversation_id':conversation.pk})
                            return redirect('chat-detail', pk=conversation.pk)
                        else:
                            logger.error("Error in creating conversation object")
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
                    return redirect('chat-detail', pk=conversation.pk)
            
            return HttpResponse("Name is required", status=400)
        return HttpResponse("Logout from admin user", status=400)




class ChatView(LoginRequiredMixin , UserPassesTestMixin , DetailView):
    model = Conversation
    template_name = 'chat.html'
    context_object_name = "conversation"

    # this function ensures that only the owner of the conversation can access it (using UserPassesTestMixin)
    def test_func(self):
        conversation = self.get_object()

        # admins can access any conversation
        if self.request.user.is_staff:
            logger.info("Staff user login")
            return True
        return conversation.user == self.request.user

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["messages"] = self.object.messages.all().order_by("created_at")
        return context
        

    
class ChatSendMessageView(UpdateView):
    """
    View for sending messages through websocket into conversation
    """
    model = Conversation
    fields = [] 

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
        logger.info(error)
        return JsonResponse(
            {"error": error},
            status=200
        )
        
    # Verify that the request is from Telegram to reject random POST requests to your webhook URL.
    secret = os.getenv('TELEGRAM_WEBHOOK_SECRET')
    if settings.DEBUG:
        secret = os.getenv('TELEGRAM_DEV_WEBHOOK_SECRET')
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

    logger.info(f'Telegram message from ID: {redact.redact_id(from_id)}')

    # Get all allowed telegram IDS (Only allowed ids can respond to user message)
    allowed_id = os.getenv('TELEGRAM_ALLOWED_USER_IDS')


    try: 
        if from_id == int(allowed_id):
            data = json.loads(request.body.decode("utf-8"))
            logger.info(f"Data file from telegram webhook:\n{redact.redact_text(data)}")
            telegram_message_processor(transaction_type=True , json_content = data)
            return JsonResponse({"result": "ok"},status=200)

    except Exception as e:
            logger.error(e)
            return JsonResponse({"result": 'ok'} , status=200)