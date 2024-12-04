from django.db import models
from django.conf import settings

# Create your models here.


class ChatBox(models.Model):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="chat_boxes",
        help_text="이 채팅박스를 소유한 사용자"
    )
    title = models.CharField(max_length=255, help_text="채팅박스 제목", default="New Chat")
    created_at = models.DateTimeField(auto_now_add=True, help_text="채팅박스 생성 시간")

    def __str__(self):
        return f"{self.user.nickname}'s ChatBox: {self.title}"


class ChatLog(models.Model):
    chatbox = models.ForeignKey(
        ChatBox,
        on_delete=models.CASCADE,
        related_name="chat_logs",
        help_text="이 채팅 로그가 속한 채팅박스"
    )
    message = models.TextField(help_text="사용자 또는 AI가 보낸 메시지 내용")
    timestamp = models.DateTimeField(auto_now_add=True, help_text="메시지가 작성된 시간")
    is_from_user = models.BooleanField(
        default=True,
        help_text="True면 사용자가 보낸 메시지, False면 AI가 보낸 메시지"
    )

    def __str__(self):
        sender = "User" if self.is_from_user else "AI"
        return f"{sender}: {self.message[:20]} ({self.timestamp})"
