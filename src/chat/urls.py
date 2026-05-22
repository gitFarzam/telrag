from django.contrib import admin
from django.urls import path
from chat.views import (
    HomeView,
    ChatView,
    ChatSendMessageView,
    DeleteConversationUserView,
    telegram_webhook,

)

urlpatterns = [
    path('', HomeView.as_view(), name='home'),
    path('chat/new/', HomeView.as_view(), name='new-conversation'),
    path('chat/<int:pk>/', ChatView.as_view(), name='chat-detail'),
    path("chat/<int:pk>/send/", ChatSendMessageView.as_view(), name="chat-send"),
    path(
        "chat/<int:pk>/delete-user/",
        DeleteConversationUserView.as_view(),
        name="chat-delete-user",
    ),
    path('webhook/', telegram_webhook, name='webhook'),

]

