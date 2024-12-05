from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi
from django.conf import settings
import openai
import random

from tmdb.models import TmdbMovie
from .models import ChatBox, ChatLog

openai.api_key = settings.OPENAI_API_KEY


class ChatWithAI(APIView):
    """
    사용자와 AI의 채팅을 처리하며,
    영화 데이터를 포함하여 AI가 직접 추천하는 로직
    """
    permission_classes = [IsAuthenticated]

    @swagger_auto_schema(
        operation_description="AI와 채팅을 통해 영화 추천을 받는 API",
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            properties={
                'message': openapi.Schema(
                    type=openapi.TYPE_STRING,
                    description='사용자가 입력한 메시지',
                    example="액션 영화 중 평점 8점 이상을 추천해줘"
                ),
            },
            required=['message'],
        ),
        responses={
            200: openapi.Response(
                description="AI 추천 결과",
                examples={
                    "application/json": {
                        "ai_response": "다크 나이트: 깊이 있는 스토리와 뛰어난 연출로 추천합니다."
                    }
                }
            ),
            400: openapi.Response(description="Bad request"),
            500: openapi.Response(description="Internal Server Error"),
        }
    )
    def post(self, request, chatbox_id):
        # 사용자 메시지
        user_message = request.data.get("message", "").strip()
        if not user_message:
            return Response({"error": "Message is required."}, status=status.HTTP_400_BAD_REQUEST)

        # ChatBox 확인
        try:
            chatbox = ChatBox.objects.get(id=chatbox_id, user=request.user)
        except ChatBox.DoesNotExist:
            return Response({"error": "ChatBox not found or access denied."}, status=status.HTTP_404_NOT_FOUND)

        # 사용자 메시지 로그 저장
        ChatLog.objects.create(
            chatbox=chatbox,
            is_from_user=True,
            message=user_message
        )

        # 평점 6.5 이상인 영화 데이터 가져오기
        movies = list(
            TmdbMovie.objects.select_related('plot')  # plot 데이터를 한 번에 가져옴
            .prefetch_related(
                'genres', 'production_companies', 'production_countries', 'spoken_languages'
            )
            .filter(vote_average__gte=6.5)
        )

        # 영화 순서를 랜덤하게 섞음
        random.shuffle(movies)

        # 리스트를 지정된 갯수만큼 줄임
        movies = movies[:50]

        # limit_length = len(movies) // 10
        # movies = movies[:limit_length]

        # 영화 데이터를 문자열로 변환
        movies_data = []
        for movie in movies:
            genres = ", ".join([genre.name for genre in movie.genres.all()])
            companies = ", ".join([company.name for company in movie.production_companies.all()])
            countries = ", ".join([country.name for country in movie.production_countries.all()])
            languages = ", ".join([language.name for language in movie.spoken_languages.all()])

            # Plot 데이터 처리
            plot_summary = (
                movie.plot.plot_summaries if hasattr(movie, "plot") and movie.plot and movie.plot.plot_summaries else "플롯 요약 정보 없음"
            )
            plot_synopsis = (
                movie.plot.plot_synopsis if hasattr(movie, "plot") and movie.plot and movie.plot.plot_synopsis else "플롯 시놉시스 정보 없음"
            )

            movies_data.append(
                f"영화 제목: {movie.title}, 장르: {genres}, 개요: {movie.overview}, "
                f"평점: {movie.vote_average}, 제작사: {companies}, 제작 국가: {countries}, 사용 언어: {languages}, "
                f"플롯 요약: {plot_summary}, 플롯 시놉시스: {plot_synopsis}"
            )

        movies_text = "\n".join(movies_data)


        # OpenAI 프롬프트 구성
        prompt = f"""
        다음은 평점 6.5 이상인 영화 데이터입니다:
        {movies_text}

        사용자 요청: "{user_message}"

        위 데이터를 기반으로 사용자의 요청에 가장 적합한 영화를 추천하고 추천 이유를 간단히 설명하세요.
        확인되지 않은 영화의 정보, 줄거리 등을 지어내지 마세요.
        응답은 항상 한국어로 작성하십시오.
        """

        # OpenAI 호출
        try:
            completion = openai.ChatCompletion.create(
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": "당신은 영화 추천 전문 AI입니다."},
                    {"role": "user", "content": prompt}
                ]
            )

            # AI 응답 처리
            ai_response = completion.choices[0].message["content"]
            if not ai_response:
                return Response({"error": "AI response was empty or malformed."}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

            # AI 응답 로그 저장
            ChatLog.objects.create(
                chatbox=chatbox,
                is_from_user=False,
                message=ai_response
            )

            return Response({
                "ai_response": ai_response,
                }, status=status.HTTP_200_OK)

        except Exception as e:
            # AI 호출 실패 시 오류 처리
            return Response({"error": f"Failed to get AI response: {str(e)}"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


# 새로운 채팅박스 생성
class CreateChatBox(APIView):
    '''
    채팅박스 생성하는 api
    '''
    @swagger_auto_schema(
        operation_description="새로운 채팅방을 생성합니다.",
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            properties={
                'title': openapi.Schema(
                    type=openapi.TYPE_STRING, 
                    description='채팅방 제목',
                    example="새 채팅"
                ),
            }
        ),
        responses={
            201: openapi.Response(
                description="채팅방 생성 성공",
                examples={
                    "application/json": {
                        "chatbox_id": 1,
                        "title": "새 채팅"
                    }
                }
            ),
            400: "잘못된 요청입니다."
        }
    )

    def post(self, request):
        user = request.user
        title = request.data.get('title', '새 채팅')
        chatbox = ChatBox.objects.create(user=user, title=title)
        return Response({"chatbox_id": chatbox.id, "title": chatbox.title}, status=status.HTTP_201_CREATED)

class UpdateChatBoxTitle(APIView):
    '''
    채팅박스 제목을 변경하는 API
    - API가 request(user) 에서 'new_title' 을 받아야 합니다.
    '''
    permission_classes = [IsAuthenticated]

    @swagger_auto_schema(
        operation_description="채팅박스 제목을 변경하는 API \n - API가 request(user) 에서 'new_title' 을 받아야 합니다.",
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            properties={
                'new_title': openapi.Schema(type=openapi.TYPE_STRING, description='New title for the chatbox'),
            },
            required=['title'],  # 필수 필드
        ),
        responses={
            200: openapi.Response(
                description="ChatBox title updated successfully.",
                examples={
                    "application/json": {
                        "message": "ChatBox title updated successfully.",
                        "chatbox_id": 1,
                        "new_title": "New Chat Title"
                    }
                }
            ),
            400: "New title is required.",
            404: "ChatBox not found or access denied.",
        }
    )

    def patch(self, request, chatbox_id):
        user = request.user
        new_title = request.data.get('new_title')

        # 새로운 제목이 제공되지 않았을 경우
        if not new_title:
            return Response({"error": "New title is required."}, status=status.HTTP_400_BAD_REQUEST)

        try:
            # 채팅박스 확인
            chatbox = ChatBox.objects.get(id=chatbox_id, user=user)
        except ChatBox.DoesNotExist:
            return Response({"error": "ChatBox not found or access denied."}, status=status.HTTP_404_NOT_FOUND)

        # 제목 변경
        chatbox.title = new_title
        chatbox.save()

        return Response({"message": "ChatBox title updated successfully.", "chatbox_id": chatbox.id, "new_title": chatbox.title}, status=status.HTTP_200_OK)


# 채팅박스 삭제
class DeleteChatBox(APIView):
    '''
    채팅박스 삭제하는 api
    '''
    permission_classes = [IsAuthenticated]

    def delete(self, request, chatbox_id):
        try:
            chatbox = ChatBox.objects.get(id=chatbox_id, user=request.user)
        except ChatBox.DoesNotExist:
            return Response({"error": "ChatBox not found or access denied."}, status=status.HTTP_404_NOT_FOUND)

        chatbox.delete()
        return Response({"message": "ChatBox deleted successfully."}, status=status.HTTP_200_OK)


# 채팅박스 목록 표시
class ListChatBoxes(APIView):
    '''
    채팅박스 목록 보여주는 api
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


# 특정 채팅박스의 로그를 가져옴
class GetChatLogs(APIView):
    '''
    채팅로그 확인용
    (채팅내용은 이걸 써서 띄우면 됨)
    '''
    permission_classes = [IsAuthenticated]

    # 채팅박스 확인
    def get(self, request, chatbox_id):
        try:
            chatbox = ChatBox.objects.get(id=chatbox_id, user=request.user)
        except ChatBox.DoesNotExist:
            return Response({"error": "ChatBox not found or access denied."}, status=status.HTTP_404_NOT_FOUND)

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