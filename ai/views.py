from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status

from kobis.models import Movie
from .models import ChatBox, ChatLog

# 프톰프트 생성
def generate_prompt_from_chatbox(chatbox):
    logs = chatbox.chat_logs.order_by('timestamp')  # 시간순으로 정렬
    log_text = "\n".join([
        f"{'User' if log.is_from_user else 'AI'}: {log.message}" for log in logs
    ])

    prompt = f"""
    Here is the chat context for ChatBox '{chatbox.title}':
    {log_text}

    Provide your response in JSON format.
    """
    return prompt

# AI 응답 생성
def generate_ai_response():
    answer = ''
    return answer


# 새로운 채팅박스 생성
class CreateChatBox(APIView):
    '''
    
    '''
    def post(self, request):
        user = request.user
        title = request.data.get('title', 'New Chat')
        chatbox = ChatBox.objects.create(user=user, title=title)
        return Response({"chatbox_id": chatbox.id, "title": chatbox.title}, status=status.HTTP_201_CREATED)

# 채팅박스 삭제
class DeleteChatBox(APIView):
    '''
    '''
    def delete(self, request, chatbox_id):
        user = request.user

        # 삭제할 채팅박스 확인
        try:
            chatbox = ChatBox.objects.get(id=chatbox_id, user=user)
        except ChatBox.DoesNotExist:
            return Response({"error": "ChatBox not found."}, status=status.HTTP_404_NOT_FOUND)

        # 채팅박스 삭제
        chatbox.delete()
        return Response({"message": "ChatBox deleted successfully."}, status=status.HTTP_200_OK)

# 채팅박스 목록 표시
class ListChatBoxes(APIView):
    '''
    '''
    def get(self, request):
        user = request.user

        # 사용자의 모든 채팅박스 가져오기
        chat_boxes = user.chat_boxes.all().order_by('-created_at')
        chatbox_data = [
            {"id": chatbox.id, "title": chatbox.title, "created_at": chatbox.created_at}
            for chatbox in chat_boxes
        ]
        return Response({"chat_boxes": chatbox_data}, status=status.HTTP_200_OK)


# 채팅 로그 처리
class ChatInBox(APIView):
    '''
    '''
    def post(self, request, chatbox_id):
        user = request.user
        message = request.data.get('message')
        
        # 해당 채팅박스를 가져오기
        try:
            chatbox = ChatBox.objects.get(id=chatbox_id, user=user)
        except ChatBox.DoesNotExist:
            return Response({"error": "ChatBox not found."}, status=status.HTTP_404_NOT_FOUND)

        # 사용자 메시지 저장
        ChatLog.objects.create(chatbox=chatbox, message=message, is_from_user=True)

        # AI 응답 생성
        ai_response = generate_ai_response(chatbox, message)

        # AI 응답 저장
        ChatLog.objects.create(chatbox=chatbox, message=ai_response, is_from_user=False)

        return Response({"user_message": message, "ai_response": ai_response}, status=status.HTTP_200_OK)


# 특정 채팅박스의 로그를 가져옴
class GetChatLogs(APIView):
    '''
    '''
    def get(self, request, chatbox_id):
        user = request.user

        # 채팅박스 확인
        try:
            chatbox = ChatBox.objects.get(id=chatbox_id, user=user)
        except ChatBox.DoesNotExist:
            return Response({"error": "ChatBox not found."}, status=status.HTTP_404_NOT_FOUND)

        # 로그 가져오기
        logs = chatbox.chat_logs.all().order_by('timestamp')
        log_data = [
            {
                "is_from_user": log.is_from_user,
                "message": log.message,
                "timestamp": log.timestamp
            }
            for log in logs
        ]
        return Response({"chatbox": chatbox.title, "logs": log_data}, status=status.HTTP_200_OK)
