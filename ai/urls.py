from django.urls import path
from .views import (
    CreateChatBox,
    UpdateChatBoxTitle,
    DeleteChatBox,
    ListChatBoxes,
    GetChatLogs,
    ChatWithAI,
)

app_name = 'chat'

urlpatterns = [
    # 채팅박스 관리
    path('api/chatbox/create/', CreateChatBox.as_view(), name='create_chatbox'),
    path('api/chatbox/list/', ListChatBoxes.as_view(), name='list_chatboxes'),
    path('api/chatbox/<int:chatbox_id>/update/', UpdateChatBoxTitle.as_view(), name='update_chatbox'),
    path('api/chatbox/<int:chatbox_id>/delete/', DeleteChatBox.as_view(), name='delete_chatbox'),

    # 채팅 로그
    path('api/chatbox/<int:chatbox_id>/log/', GetChatLogs.as_view(), name='chat_log'),

    # 채팅 API
    path('api/chatbot/<int:chatbox_id>', ChatWithAI.as_view(), name='chatbot'), 
]

