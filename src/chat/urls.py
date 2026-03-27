from django.contrib import admin
from django.urls import path
from chat.views import NewConversationView,ChatView,ChatSendMessageView, telegram_webhook

urlpatterns = [
    path('', NewConversationView.as_view(), name='home'),
    path('chat/new/', NewConversationView.as_view(), name='new-conversation'),
    path('chat/<int:pk>/', ChatView.as_view(), name='chat-detail'),
    path("chat/<int:pk>/send/", ChatSendMessageView.as_view(), name="chat-send"),
    path('webhook/', telegram_webhook, name='webhook')
]