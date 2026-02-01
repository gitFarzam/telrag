from django.template.loader import render_to_string
from django.shortcuts import render, redirect
from .models import Conversation, Message
from django.views.generic import DetailView, UpdateView
from django.http import HttpResponse
from asgiref.sync import async_to_sync
from channels.layers import get_channel_layer

# Create your views here.
class ChatView(DetailView):
    model = Conversation
    template_name = 'chat.html'
    context_object_name = "conversation"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["messages"] = self.object.messages.select_related("user")
        return context

    
class ChatSendMessageView(UpdateView):
    model = Conversation
    fields = []  # we are not editing Conversation fields

    def form_valid(self, form):
        conversation = self.get_object()
        content = self.request.POST.get("content")

        if content:
            message =Message.objects.create(
                conversation=conversation,
                user=self.request.user,
                content=content,
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