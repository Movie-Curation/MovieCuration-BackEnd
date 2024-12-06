from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework import status, permissions
from rest_framework.permissions import IsAuthenticated
from rest_framework_simplejwt.tokens import RefreshToken
from django.db import models

from rest_framework_simplejwt.authentication import JWTAuthentication  #로그인 체크인증

from rest_framework.permissions import AllowAny
from django.db.models import Avg, Count                    #평균 ,수
from .serializer import ReviewStatisticsSerializer         #평균 별점

from .models import Favorite, User, Follow
from .serializer import UserRegisterSerializer, UserProfileSerializer, FollowSerializer, FavoriteSerializer, ReviewSerializer
from django.shortcuts import get_object_or_404
from drf_yasg import openapi
from drf_yasg.utils import swagger_auto_schema

from .models import Comment                                #댓글기능
from .serializer import CommentSerializer
from .serializer import ReviewSerializer                   #리뷰 직렬화 추가
from .models import Movie , TmdbMovie
from  kobis.models import Movie
from .serializer import MovieSerializer  #영화 불러오기

from .models import ReviewReaction
from .serializer import ReviewReactionSerializer            #리뷰 좋아요/싫어요

from .models import Review, ReviewReport
from .serializer import ReviewReportSerializer                 #리뷰 신고

from django.db.models import Count    #리뷰 좋아요 카운트


import json
from django.http import JsonResponse
from graphviz import Digraph                                  #깃플로우 자동JSOn코드

from .permissions import IsExpertUser, IsAdminUser, IsRegularUser
from rest_framework.permissions import IsAuthenticated


class LogoutAPIView(APIView): 
    """
    사용자 로그아웃.

    사용자의 액세스 토큰 및 리프레시 토큰을 블랙리스트에 등록하여 로그아웃합니다.
    """
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        try:
            refresh_token = request.data.get("refresh")
            if not refresh_token:
                return Response({"error": "Refresh token is required."}, status=status.HTTP_400_BAD_REQUEST)

            token = RefreshToken(refresh_token)
            token.blacklist()

            return Response({"message": "Logged out successfully."}, status=status.HTTP_205_RESET_CONTENT)
        except Exception:
            return Response(
                {"error": "Invalid token or token has already been blacklisted."},
                status=status.HTTP_400_BAD_REQUEST,
            )


class RegisterUserAPIView(APIView):
    @swagger_auto_schema(
        request_body=UserRegisterSerializer,
        responses={
            201: "User registered successfully.",
            400: "Validation error.",
        },
    )
    def post(self, request):
        """
        새로운 사용자 등록.

        신규 유저를 회원으로 등록합니다.
        """
        serializer = UserRegisterSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response({"message": "User registered successfully."}, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    

class CheckLoginAPIView(APIView):
    """
    현재 사용자의 로그인 상태를 확인하는 API.
    """
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated]

    def get(self, request):
        user = request.user
        return Response({
            "is_logged_in": True,
            "user": {
                "username": user.userid,
                "email": user.email,
            },
            "is_admin": user.is_staff,
        })


class UserProfileUpdateView(APIView):
    permission_classes = [IsAuthenticated]

    def put(self, request):
        """
        사용자 프로필 업데이트

        사용자의 프로필 정보를 수정합니다.
        """
        user = request.user
        genres = request.data.pop("genres", None)  # genres를 별도로 처리
        serializer = UserProfileSerializer(user, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()

            # ManyToManyField 갱신
            if genres is not None:
                user.genres.set(genres)  # 새로운 장르 리스트로 설정
            return Response(serializer.data, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
class CommentCreateAPIView(APIView):
    permission_classes = [IsAuthenticated]

    
    @swagger_auto_schema(
        request_body=CommentSerializer,
        responses={
            201: "댓글 생성 성공",
            400: "유효성 검사 실패",
        }
    )

    def post(self, request, review_id):
        """
        리뷰에 댓글 추가.

        특정 리뷰에 새로운 댓글을 작성합니다.
        """
        review = get_object_or_404(Review, id=review_id)  # 리뷰가 존재하는지 확인
        serializer = CommentSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save(user=request.user, review=review)  # 사용자와 리뷰를 설정하여 저장
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class CommentListAPIView(APIView):
    
    @swagger_auto_schema(
        responses={
            200: "댓글 목록 반환 성공",
            404: "리뷰 없음",
        }
    )

    def get(self, request, review_id):
        """
        리뷰의 모든 댓글 조회.

        특정 리뷰에 작성된 모든 댓글을 반환합니다.
        """
        review = get_object_or_404(Review, id=review_id)
        comments = Comment.objects.filter(review=review)
        serializer = CommentSerializer(comments, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)


class CommentUpdateAPIView(APIView):
    
    permission_classes = [IsAuthenticated]

    def put(self, request, comment_id):
        """
        댓글 업데이트.

        댓글 ID를 기반으로 댓글의 내용을 수정합니다.
        """
        comment = get_object_or_404(Comment, id=comment_id, user=request.user)  # 작성자가 본인인지 확인
        serializer = CommentSerializer(comment, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class CommentDeleteAPIView(APIView):
    """
    특정 댓글 삭제.

    댓글 ID를 기반으로 댓글을 삭제합니다.
    """
    permission_classes = [IsAuthenticated]

    def delete(self, request, comment_id):
        """
        특정 댓글 삭제.

        댓글 ID를 기반으로 댓글을 삭제합니다.
        """
        comment = get_object_or_404(Comment, id=comment_id, user=request.user)  # 작성자가 본인인지 확인
        comment.delete()
        return Response({"message": "Comment deleted successfully."}, status=status.HTTP_204_NO_CONTENT)
    
class ReviewCreateAPIView(APIView):
    permission_classes = [IsAuthenticated]

    @swagger_auto_schema(
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            properties={
                'movieCd': openapi.Schema(type=openapi.TYPE_INTEGER, description='영화 ID'),
                'rating': openapi.Schema(type=openapi.TYPE_NUMBER, format='float', description='평점 (0.0 ~ 10.0)'),
                'comment': openapi.Schema(type=openapi.TYPE_STRING, description='리뷰 내용 (선택)'),
            },
            required=['movieCd', 'rating'],  # 필수 필드
        ),
        responses={201: "리뷰 작성 성공", 400: "요청 유효성 검사 실패"},
    )
    def post(self, request):
        """
        리뷰 작성.

        특정 영화에 대한 리뷰를 작성합니다.
        """
        movieCd = request.data.get("movieCd")

        # movieCd 유효성 확인
        if not movieCd:
            return Response({"error": "movieCd is required"}, status=status.HTTP_400_BAD_REQUEST)

        # movieCd를 숫자로 변환 (문자열로 전달된 경우 대비)
        try:
            movieCd = int(movieCd)
        except (ValueError, TypeError):
            return Response(
                {"error": "Invalid movieCd. It must be an integer."},
                status=status.HTTP_400_BAD_REQUEST
            )

        # 데이터베이스에서 영화 조회
        movie = get_object_or_404(Movie, movieCd=movieCd)

        # 유저가 이미 리뷰를 작성했는지 확인
        if Review.objects.filter(user=request.user, movie=movie).exists():
            return Response({"error": "You have already reviewed this movie."}, status=status.HTTP_400_BAD_REQUEST)

        # 리뷰 데이터 준비
        review_data = {
            "movieCd": movieCd,
            "rating": request.data.get("rating"),
            "comment": request.data.get("comment", ""),
        }

        # 직렬화 및 저장
        serializer = ReviewSerializer(data=review_data)
        if serializer.is_valid():
            serializer.save(user=request.user, movie=movie)
            return Response(serializer.data, status=status.HTTP_201_CREATED)

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    


class ReviewUpdateAPIView(APIView):           #리뷰  평점,댓글 수정
    
    permission_classes = [IsAuthenticated]

    def put(self, request, review_id):
        """
        리뷰 수정.

        특정 리뷰의 내용을 업데이트합니다.
        """
        
        # 리뷰 존재 여부 및 작성자 확인
        review = get_object_or_404(Review, id=review_id, user=request.user)

        serializer = ReviewSerializer(review, data=request.data, partial=True)  # partial=True는 일부 필드만 수정 허용
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_200_OK)

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
class ReviewDeleteAPIView(APIView):
    
    permission_classes = [IsAuthenticated]

    def delete(self, request, review_id):
        """
        리뷰 삭제.

        특정 리뷰를 삭제합니다.
        """

        # 리뷰 존재 여부 및 작성자 확인
        review = get_object_or_404(Review, id=review_id, user=request.user)

        review.delete()  # 리뷰 삭제
        return Response({"message": "Review deleted successfully."}, status=status.HTTP_204_NO_CONTENT)


class MovieReviewsAPIView(APIView):
    
    permission_classes = [IsAuthenticated]

    def get(self, request, movieCd):
        """
        특정 영화에 대한 모든 리뷰 조회

        특정 영화 ID를 기반으로 해당 영화의 리뷰를 반환합니다.
        """
        movie = get_object_or_404(Movie.objects.prefetch_related('genres'), movieCd=movieCd)
        reviews = Review.objects.filter(movie=movie)
        if not reviews.exists():
            return Response({"message": "No reviews found for this movie."}, status=status.HTTP_404_NOT_FOUND)
        serializer = ReviewSerializer(reviews, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)
    
    
class MovieReviewStatisticsAPIView(APIView):
    permission_classes = [AllowAny]

    def get(self, request, movieCd):
        """
        특정 영화의 리뷰 통계.

        특정 영화에 대한 평균 평점 및 리뷰 개수를 반환합니다.
        """
        movie = get_object_or_404(Movie.objects.prefetch_related('genres'), movieCd=movieCd)
        reviews = Review.objects.filter(movie=movie)

        if not reviews.exists():
            return Response(
                {"error": f"No reviews found for movie ID {movieCd}."},
                status=status.HTTP_404_NOT_FOUND,
            )

        statistics = reviews.aggregate(
            average_rating=Avg('rating'),
            review_count=Count('id')
        )

        data = {
        "movieCd": movie.id,
        "global_vote_average": movie.vote_average,  # TMDB 또는 외부 데이터베이스의 글로벌 평균 평점
        "genres": [genre.name for genre in movie.genres.all()],  # genres 리스트
        "local_average_rating": statistics['average_rating'],  # 앱 사용자들의 리뷰 평균 평점
        "review_count": statistics['review_count'],
}
        return Response(data, status=status.HTTP_200_OK)


class UserReviewsAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        """
        사용자가 작성한 리뷰 조회.

        로그인한 사용자가 작성한 모든 리뷰를 반환합니다.
        """
        reviews = Review.objects.filter(user=request.user)
        if not reviews.exists():
            return Response({"message": "You have not written any reviews yet."}, status=status.HTTP_404_NOT_FOUND)
        serializer = ReviewSerializer(reviews, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)

class ReviewListSortedAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        """
        정렬된 리뷰 조회.

        요청된 기준(예: 평점, 작성일)에 따라 리뷰를 정렬하여 반환합니다.
        """
        sort_by = request.query_params.get("sort_by", "created_at")
        order = request.query_params.get("order", "desc")

        if order == "desc":
            sort_by = f"-{sort_by}"

        allowed_sort_fields = ["created_at", "rating", "updated_at"]
        if sort_by.lstrip("-") not in allowed_sort_fields:
            return Response(
                {"error": "Invalid sort field. Allowed fields: created_at, rating, updated_at."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        reviews = Review.objects.all().order_by(sort_by)
        serializer = ReviewSerializer(reviews, many=True)

        return Response(serializer.data, status=status.HTTP_200_OK)
    
class ReviewReactionAPIView(APIView):    #리뷰 좋아요/싫어요
    permission_classes = [IsAuthenticated]

    def post(self, request, review_id):
        """
        리뷰에 좋아요/싫어요 추가

        특정 리뷰에 좋아요 또는 싫어요를 추가합니다.
        """
        reaction = request.data.get('reaction')
        if reaction not in [ReviewReaction.LIKE, ReviewReaction.DISLIKE]:
            return Response({"error": "Invalid reaction type. Use 'like' or 'dislike'."},
                            status=status.HTTP_400_BAD_REQUEST)

        review = Review.objects.filter(id=review_id).first()
        if not review:
            return Response({"error": "Review not found."}, status=status.HTTP_404_NOT_FOUND)

        # 중복 반응 방지
        existing_reaction = ReviewReaction.objects.filter(user=request.user, review=review).first()
        if existing_reaction:
            if existing_reaction.reaction == reaction:
                return Response({"error": f"You already reacted with '{reaction}' to this review."},
                                status=status.HTTP_400_BAD_REQUEST)
            else:
                # 반응을 업데이트
                existing_reaction.reaction = reaction
                existing_reaction.save()
                return Response({"message": f"Your reaction has been updated to '{reaction}'."},
                                status=status.HTTP_200_OK)

        # 새로운 반응 생성
        new_reaction = ReviewReaction.objects.create(user=request.user, review=review, reaction=reaction)
        serializer = ReviewReactionSerializer(new_reaction)
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    def get(self, request, review_id):
        """
        리뷰의 좋아요/싫어요 수 조회

        특정 리뷰의 좋아요 및 싫어요 개수 조회
        """
        review = Review.objects.filter(id=review_id).first()
        if not review:
            return Response({"error": "Review not found."}, status=status.HTTP_404_NOT_FOUND)

        like_count = ReviewReaction.objects.filter(review=review, reaction=ReviewReaction.LIKE).count()
        dislike_count = ReviewReaction.objects.filter(review=review, reaction=ReviewReaction.DISLIKE).count()

        return Response({"review_id": review.id, "likes": like_count, "dislikes": dislike_count},
                        status=status.HTTP_200_OK)
    
class PromoteToExpertAPIView(APIView):                                               
    
    permission_classes = [IsAuthenticated, IsAdminUser]  # 관리자만 호출 가능

    def post(self, request):

        """
        리뷰 좋아요가 100개 이상인 작성자를 전문가로 승격

        리뷰에 좋아요가 일정 개수(예: 100개)를 넘은 사용자를 전문가로 승격합니다.
        """
        reviews = Review.objects.annotate(
            like_count=Count('reactions', filter=models.Q(reactions__reaction=ReviewReaction.LIKE))
        ).filter(like_count__gte=100)

        promoted_users = []
        for review in reviews:
            user = review.user
            if not user.is_expert:
                user.is_expert = True
                user.save()
                promoted_users.append(user.userid)

        if promoted_users:
            return Response(
                {
                    "message": "Promoted users to experts successfully.",
                    "promoted_users": promoted_users,
                },
                status=status.HTTP_200_OK,
            )
        else:
            return Response(
                {"message": "No users qualified for promotion."},
                status=status.HTTP_200_OK,
            )


class AdminControlAPIView(APIView):
    
    permission_classes = [IsAuthenticated, IsAdminUser]

    @swagger_auto_schema(
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            properties={
                'user_id': openapi.Schema(type=openapi.TYPE_INTEGER, description="ID of the user"),
                'action': openapi.Schema(type=openapi.TYPE_STRING, description="Action to perform (e.g., promote/demote)"),
                'role': openapi.Schema(type=openapi.TYPE_STRING, description="Role to assign (e.g., expert, regular)"),
            },
            required=['user_id', 'action'],  # 필수 필드 지정
        ),
        responses={
            200: openapi.Response("Admin action performed successfully."),
            400: openapi.Response("Invalid input data."),
            403: openapi.Response("Permission denied."),
        }
    )
    def post(self, request):
        """
        새로운 관리자를 생성합니다.

        관리자 권한으로 특정 사용자에 대해 조치를 수행합니다.
        """
        user_id = request.data.get('user_id')
        action = request.data.get('action')
        role = request.data.get('role', None)

        if not user_id or not action:
            return Response({"error": "user_id and action are required fields."}, status=status.HTTP_400_BAD_REQUEST)

        # 사용자 조회
        user = get_object_or_404(User, id=user_id)

        # 액션 처리
        if action == "promote":
            if role == "expert":
                user.is_expert = True
                user.save()
                return Response({"message": f"User {user.userid} has been promoted to Expert."}, status=status.HTTP_200_OK)
            elif role == "admin":
                user.is_admin = True
                user.save()
                return Response({"message": f"User {user.userid} has been promoted to Admin."}, status=status.HTTP_200_OK)
            else:
                return Response({"error": "Invalid role specified."}, status=status.HTTP_400_BAD_REQUEST)

        elif action == "demote":
            if role == "expert":
                user.is_expert = False
                user.save()
                return Response({"message": f"User {user.userid} has been demoted from Expert."}, status=status.HTTP_200_OK)
            elif role == "admin":
                user.is_admin = False
                user.save()
                return Response({"message": f"User {user.userid} has been demoted from Admin."}, status=status.HTTP_200_OK)
            else:
                return Response({"error": "Invalid role specified."}, status=status.HTTP_400_BAD_REQUEST)

        else:
            return Response({"error": "Invalid action specified."}, status=status.HTTP_400_BAD_REQUEST)

class RegularReviewAPIView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    @swagger_auto_schema(
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            properties={
                'movieCd': openapi.Schema(type=openapi.TYPE_INTEGER, description='영화 ID'),
                'rating': openapi.Schema(type=openapi.TYPE_NUMBER, format='float', description='평점 (0.0 ~ 10.0)'),
                'comment': openapi.Schema(type=openapi.TYPE_STRING, description='리뷰 내용 (선택)'),
            },
            required=['movieCd', 'rating'],  # 필수 필드
        ),
        responses={
            201: "리뷰 작성 성공",
            400: "요청 유효성 검사 실패",
        },
    )
    def post(self, request):
        """
        일반 사용자 리뷰 작성 로직

        일반 사용자가 새로운 리뷰를 작성합니다.
        """
        movieCd = request.data.get("movieCd")
        if not movieCd:
            return Response({"error": "movieCd is required"}, status=status.HTTP_400_BAD_REQUEST)

        # 중복 리뷰 방지
        if Review.objects.filter(user=request.user, movieCd=movieCd).exists():
            return Response({"error": "You have already reviewed this movie."}, status=status.HTTP_400_BAD_REQUEST)

        # `is_expert_review`는 강제로 False로 설정
        review_data = request.data.copy()
        review_data['is_expert_review'] = False

        serializer = ReviewSerializer(data=review_data)
        if serializer.is_valid():
            # user를 추가하고 저장
            serializer.save(user=request.user)
            return Response(serializer.data, status=status.HTTP_201_CREATED)

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)



class ExpertReviewAPIView(APIView):
    """
    전문가 리뷰 생성 및 조회
    """
    permission_classes = [IsAuthenticated, IsExpertUser]

    @swagger_auto_schema(
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            properties={
                'movieCd': openapi.Schema(type=openapi.TYPE_INTEGER, description='영화 ID'),
                'rating': openapi.Schema(type=openapi.TYPE_NUMBER, format='float', description='평점 (0.0 ~ 10.0)'),
                'comment': openapi.Schema(type=openapi.TYPE_STRING, description='리뷰 내용 (선택)'),
            },
            required=['movieCd', 'rating'],  # 필수 필드
        ),
        responses={
            201: "리뷰 작성 성공",
            400: "요청 유효성 검사 실패",
        },
    )
    def post(self, request):
        """
        전문가 리뷰 작성 

        전문가가 작성 로직
        """
        movieCd = request.data.get("movieCd")
        if not movieCd:
            return Response({"error": "movieCd is required"}, status=status.HTTP_400_BAD_REQUEST)

        # 중복 리뷰 방지
        if Review.objects.filter(user=request.user, movieCd=movieCd, is_expert_review=True).exists():
            return Response({"error": "You have already reviewed this movie as an expert."}, status=status.HTTP_400_BAD_REQUEST)

        # `is_expert_review` 강제 설정
        review_data = request.data.copy()
        review_data['is_expert_review'] = True

        serializer = ReviewSerializer(data=review_data)
        if serializer.is_valid():
            # user를 추가하고 저장
            serializer.save(user=request.user)
            return Response(serializer.data, status=status.HTTP_201_CREATED)

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def get(self, request):
        """
        전문가 리뷰 조회

        전문가 리뷰 전체를 조회
        """
        expert_reviews = Review.objects.filter(is_expert_review=True)
        serializer = ReviewSerializer(expert_reviews, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)

class ReviewReportAPIView(APIView):
    """
    리뷰 신고 기능
    """
    permission_classes = [IsAuthenticated]

    @swagger_auto_schema(
        operation_description="리뷰 신고 API",
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            properties={
                'reason': openapi.Schema(type=openapi.TYPE_STRING, description="신고 이유"),
                'description': openapi.Schema(type=openapi.TYPE_STRING, description="추가 설명 (선택)"),
            },
            required=['reason']
        ),
        responses={201: "Review reported successfully.", 400: "Validation failed."}
    )

    def post(self, request, review_id):
        """
        리뷰를 신고하는 기능
        """
        review = get_object_or_404(Review, id=review_id)
        serializer = ReviewReportSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save(user=request.user, review=review)  # 신고한 사용자 및 리뷰 저장
            return Response({"message": "Review reported successfully."}, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        

class FollowAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def get_follow_relationship(self, from_user, to_user):
        """
        팔로우 관계를 확인하는 헬퍼 메서드.
        """
        return Follow.objects.filter(from_user=from_user, to_user=to_user).first()

    def post(self, request, user_id):
        """
        특정 사용자 팔로우.

        user_id에 해당하는 사용자를 팔로우합니다.
        """
        to_user = get_object_or_404(User, id=user_id)

        if self.get_follow_relationship(request.user, to_user):
            return Response(
                {"message": "이미 이 사용자를 팔로우하고 있습니다."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        follow = Follow.objects.create(from_user=request.user, to_user=to_user)
        serializer = FollowSerializer(follow)
        return Response(
            {"message": "팔로우가 완료되었습니다.", "data": serializer.data},
            status=status.HTTP_201_CREATED,
        )

    def delete(self, request, user_id):
        """
        특정 사용자 언팔로우.

        user_id에 해당하는 사용자에 대한 팔로우를 취소합니다.
        """
        to_user = get_object_or_404(User, id=user_id)

        follow = self.get_follow_relationship(request.user, to_user)
        if not follow:
            return Response(
                {"message": "이 사용자를 팔로우하고 있지 않습니다."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        follow.delete()
        return Response(
            {"message": "언팔로우가 완료되었습니다."},
            status=status.HTTP_200_OK,
        )

    def get(self, request):
        """
        팔로워 또는 팔로잉 목록 조회.

        쿼리 파라미터 `type`에 따라 반환:
        - `type=followers`: 사용자를 팔로우하는 목록
        - `type=following`: 사용자가 팔로우하고 있는 목록
        """
        follow_type = request.query_params.get("type")
        if follow_type == "followers":
            queryset = Follow.objects.filter(to_user=request.user)
            serializer = FollowSerializer(queryset, many=True)
            return Response(
                {"message": "팔로워 목록 조회 성공", "data": serializer.data},
                status=status.HTTP_200_OK,
            )
        elif follow_type == "following":
            queryset = Follow.objects.filter(from_user=request.user)
            serializer = FollowSerializer(queryset, many=True)
            return Response(
                {"message": "팔로잉 목록 조회 성공", "data": serializer.data},
                status=status.HTTP_200_OK,
            )
        else:
            return Response(
                {"error": "유효하지 않은 쿼리 파라미터입니다. 'type=followers' 또는 'type=following'을 사용하세요."},
                status=status.HTTP_400_BAD_REQUEST,
            )


class FollowingListView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        """
        사용자가 팔로우하는 목록 조회

        사용자의 팔로우 목록을 나열합니다
        """
        following = Follow.objects.filter(from_user=request.user)
        serializer = FollowSerializer(following, many=True)
        return Response(
            {"message": "Following list retrieved successfully.", "data": serializer.data},
            status=status.HTTP_200_OK,
        )


class FollowersListView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        """
        사용자를 팔로우하는 사용자 목록 조회

        사용자를 팔로우하는 사용자 목록 조회
        """
        followers = Follow.objects.filter(to_user=request.user)
        serializer = FollowSerializer(followers, many=True)
        return Response(
            {"message": "Followers list retrieved successfully.", "data": serializer.data},
            status=status.HTTP_200_OK,
        )

class FavoriteAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, movieCd=None):
        """
        즐겨찾기 목록 조회.

        사용자 즐겨찾기 영화 목록 반환.
        """
        if movieCd:
            favorite = Favorite.objects.filter(user=request.user, movie__movieCd=movieCd).select_related('movie').first()
            if not favorite:
                return Response({"error": "Movie not found"}, status=status.HTTP_404_NOT_FOUND)

            movie = favorite.movie
            data = {
                "movieCd": movie.movieCd,  # movieCd로 반환
                "movie_name": movie.movieNm,
                "vote_average": movie.vote_average,
                "genres": [genre.name for genre in movie.genres.all()],
            }
            return Response({"favorite": data}, status=status.HTTP_200_OK)

        favorites = Favorite.objects.filter(user=request.user).select_related('movie')
        data = [
            {
                "movieCd": favorite.movie.movieCd,  # movieCd로 반환
                "movie_name": favorite.movie.movieNm,
                "vote_average": favorite.movie.vote_average,
                "genres": [genre.name for genre in favorite.movie.genres.all()],
            }
            for favorite in favorites
        ]
        return Response({"favorites": data}, status=status.HTTP_200_OK)

    @swagger_auto_schema(
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            properties={
                'movieCd': openapi.Schema(type=openapi.TYPE_INTEGER, description='영화 코드 (movieCd)'),
            },
            required=['movieCd'],  # 필수 필드
        ),
        responses={
            201: "Movie added to favorites successfully.",
            400: "Movie already exists in favorites.",
        },
    )
    def post(self, request):
        """
        영화 즐겨찾기 추가

        특정 영화를 즐겨찾기에 추가합니다.
        """
        movieCd = request.data.get("movieCd")
        if not movieCd:
            return Response({"error": "movieCd is required"}, status=status.HTTP_400_BAD_REQUEST)

        try:
            movie = Movie.objects.get(movieCd=movieCd)
        except Movie.DoesNotExist:
            return Response({"error": "Movie not found"}, status=status.HTTP_404_NOT_FOUND)

        if Favorite.objects.filter(user=request.user, movie=movie).exists():
            return Response({"error": "Already added to favorites"}, status=status.HTTP_400_BAD_REQUEST)

        favorite = Favorite.objects.create(user=request.user, movie=movie)
        serializer = FavoriteSerializer(favorite)
        return Response(
            {"message": "Movie added to favorites successfully.", "data": serializer.data},
            status=status.HTTP_201_CREATED,
        )

    def delete(self, request, movieCd):
        """
        특정 영화 즐겨찾기 삭제

        유저의 특정 영화 즐겨찾기 데이터를 삭제합니다.
        """
        try:
            movie = Movie.objects.get(movieCd=movieCd)
        except Movie.DoesNotExist:
            return Response({"error": "Movie not found"}, status=status.HTTP_404_NOT_FOUND)

        favorite = Favorite.objects.filter(user=request.user, movie=movie).first()
        if not favorite:
            return Response({"error": "Favorite not found"}, status=status.HTTP_404_NOT_FOUND)

        favorite.delete()
        return Response(
            {"message": "Removed from favorites successfully."},
            status=status.HTTP_200_OK,
        )



class MovieListAPIView(APIView):
    permission_classes = [AllowAny]

    def get(self, request):
        """
        모든 영화 목록 조회.

        데이터베이스에 저장된 모든 영화의 리스트를 반환합니다.
        """
        movies = Movie.objects.prefetch_related('genres').all()
        serializer = MovieSerializer(movies, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)


class MovieDetailsAPIView(APIView):
    permission_classes = [AllowAny]

    def get(self, request, movieCd):
        """
        특정 영화 정보 조회.

        영화 코드 (movieCd)를 기반으로 영화 정보를 반환합니다.
        """
        movie = get_object_or_404(Movie.objects.prefetch_related('genres'), movieCd=movieCd)
        serializer = MovieSerializer(movie)
        return Response(serializer.data, status=status.HTTP_200_OK)

class UserProfileView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        """
        사용자 프로필 조회

        로그인한 사용자의 프로필 정보를 반환합니다.
        """
        user = request.user
        user_data = {
            "userid": user.userid,
            "email": user.email,
            "name": user.name,
            "gender": user.gender,
            "genres": list(user.genres.values("id", "name")),  # ManyToManyField 직렬화
            "nickname": user.nickname,
        }
        return Response(
            {"message": "User profile retrieved successfully.", "data": user_data},
            status=status.HTTP_200_OK,
        )
    
def generate_diagram(request):

    
    # Swagger JSON 파일 경로
    swagger_path = "staticfiles/swagger.json"  # Swagger JSON 파일을 여기에 저장

    try:
        # Swagger 문서 읽기 (UTF-8로 인코딩 지정)
        with open(swagger_path, 'r', encoding='utf-8') as f:
            swagger_data = json.load(f)
    except FileNotFoundError:
        return JsonResponse({"error": "Swagger JSON 파일을 찾을 수 없습니다."}, status=404)
    except UnicodeDecodeError:
        return JsonResponse({"error": "Swagger JSON 파일의 인코딩이 올바르지 않습니다. UTF-8 인코딩을 사용하세요."}, status=500)

    # API 경로와 메서드 추출
    api_paths = extract_api_paths(swagger_data)

    # 다이어그램 생성
    create_git_flow_diagram(api_paths)

    return JsonResponse({"message": "Swagger 다이어그램이 생성되었습니다.", "path": "staticfiles/api_git_flow_diagram.png"})


def extract_api_paths(swagger_data):
    """
    Swagger 문서에서 API 경로와 메서드를 추출합니다.
    """
    api_paths = []
    for path, methods in swagger_data.get("paths", {}).items():
        for method in methods.keys():
            api_paths.append((method.upper(), path))
    return api_paths


def create_git_flow_diagram():
    """
    Git Flow 스타일의 API 다이어그램 생성
    """
    dot = Digraph(comment="Git Flow Diagram", graph_attr={"rankdir": "LR"})  # 좌에서 우로 방향 설정

    # Main 브랜치
    with dot.subgraph(name="cluster_main") as main:
        main.attr(label="Main", style="filled", color="lightblue")
        main.node("main1", "POST /api/accounts/admin/")
        main.node("main2", "GET /api/accounts/profile/")

    # Develop 브랜치
    with dot.subgraph(name="cluster_develop") as develop:
        develop.attr(label="Develop", style="filled", color="mediumpurple")
        develop.node("develop1", "PUT /api/accounts/admin/reports/")

    # Feature 브랜치 1
    with dot.subgraph(name="cluster_feature1") as feature1:
        feature1.attr(label="Feature: Comments", style="filled", color="mediumseagreen")
        feature1.node("feature1_1", "POST /api/comments/")
        feature1.node("feature1_2", "DELETE /api/comments/{id}/")

    # Feature 브랜치 2
    with dot.subgraph(name="cluster_feature2") as feature2:
        feature2.attr(label="Feature: Favorites", style="filled", color="mediumseagreen")
        feature2.node("feature2_1", "GET /api/accounts/favorites/")
        feature2.node("feature2_2", "POST /api/accounts/favorites/")

    # Release 브랜치
    with dot.subgraph(name="cluster_release") as release:
        release.attr(label="Release", style="filled", color="lightskyblue")
        release.node("release1", "GET /api/accounts/reviews/")
        release.node("release2", "GET /api/accounts/reviews/sorted/")

    # Hotfix 브랜치
    with dot.subgraph(name="cluster_hotfix") as hotfix:
        hotfix.attr(label="Hotfix", style="filled", color="salmon")
        hotfix.node("hotfix1", "POST /api/token/")
        hotfix.node("hotfix2", "POST /api/token/refresh/")

    # 브랜치 연결
    dot.edge("main1", "develop1", label="Branch from Main")
    dot.edge("develop1", "feature1_1", label="Branch to Feature 1")
    dot.edge("develop1", "feature2_1", label="Branch to Feature 2")
    dot.edge("feature1_2", "develop1", label="Merge Feature 1")
    dot.edge("feature2_2", "develop1", label="Merge Feature 2")
    dot.edge("develop1", "release1", label="Prepare Release")
    dot.edge("release2", "main2", label="Release to Main")
    dot.edge("hotfix1", "main1", label="Hotfix")

    # 다이어그램 저장
    diagram_path = "staticfiles/git_flow_diagram"
    dot.render(diagram_path, format="png", cleanup=True)

class GitFlowDiagramAPIView(APIView):
    """
    Swagger 기반 Git Flow 스타일 다이어그램 생성 API
    """
    permission_classes = [IsAuthenticated]

    def get(self, request):
        swagger_path = "staticfiles/swagger.json"

        try:
            with open(swagger_path, 'r', encoding='utf-8') as f:
                swagger_data = json.load(f)
        except FileNotFoundError:
            return Response({"error": "Swagger JSON 파일을 찾을 수 없습니다."}, status=status.HTTP_404_NOT_FOUND)
        except json.JSONDecodeError:
            return Response({"error": "Swagger JSON 파일이 잘못된 형식입니다."}, status=status.HTTP_400_BAD_REQUEST)

        # API 경로 및 메서드 추출
        api_paths = self.extract_api_paths(swagger_data)

        # 다이어그램 생성
        diagram_path = self.create_git_flow_diagram(api_paths)

        return Response({"message": "Diagram created successfully.", "diagram_path": diagram_path}, status=status.HTTP_200_OK)

    def extract_api_paths(self, swagger_data):
        """
        Swagger JSON 문서에서 API 경로 및 메서드를 추출
        """
        api_paths = []
        for path, methods in swagger_data.get("paths", {}).items():
            for method in methods.keys():
                api_paths.append((method.upper(), path))
        return api_paths

    def create_git_flow_diagram(self, api_paths):
        """
        Git Flow 스타일 다이어그램 생성
        """
        dot = Digraph(comment="Git Flow Diagram", graph_attr={"rankdir": "LR"})

        # Git Flow 구성 요소
        dot.node("main", "Main", shape="box", style="filled", color="lightblue")
        dot.node("develop", "Develop", shape="box", style="filled", color="mediumpurple")
        dot.node("feature1", "Feature 1: Comments", shape="ellipse", style="filled", color="mediumseagreen")
        dot.node("feature2", "Feature 2: Favorites", shape="ellipse", style="filled", color="mediumseagreen")
        dot.node("release", "Release", shape="box", style="filled", color="lightskyblue")
        dot.node("hotfix", "Hotfix", shape="box", style="filled", color="salmon")

        # 경로 추가
        for method, path in api_paths:
            label = f"{method} {path}"
            dot.node(label, label, shape="plaintext")
            dot.edge("develop", label)

        # 다이어그램 저장
        diagram_path = "staticfiles/git_flow_diagram.png"
        dot.render(diagram_path, format="png", cleanup=True)
        return diagram_path