from django.template.loader import render_to_string
from django.shortcuts import render, redirect
from .models import Conversation, Message
from django.views.generic import DetailView, UpdateView,TemplateView
from core.models import User
from django.http import HttpResponse
from asgiref.sync import async_to_sync
from channels.layers import get_channel_layer
import uuid
from django.contrib.auth import authenticate,login
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin


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
        is_agent = self.request.POST.get("is_agent" , False)
        if is_agent in ["true" , "True" , "1"]:
            is_agent = True

        if content:
            message =Message.objects.create(
                conversation=conversation,
                content=content,
                is_agent=is_agent
            )
            html = render_to_string(
                "message.html",
                {"message": message, "request": self.request}
            )

            oob_html = (
                '<div id="messages" hx-swap-oob="beforeend" class="chat-container">'
                + html
                + "</div>"
            )

            channel_layer = get_channel_layer()
            async_to_sync(channel_layer.group_send)(
                f"chatgroup_{conversation.pk}",
                {"type": "message_handler", "html_response": oob_html},
            )

            return HttpResponse(status=204)

        return HttpResponse("")
    

