from django.contrib import admin
from django.urls import path
from chat.views import ChatView,ChatSendMessageView

urlpatterns = [
    path('<int:pk>/', ChatView.as_view(), name='chat-detail'),
    path("<int:pk>/send/", ChatSendMessageView.as_view(), name="chat-send"),
]
