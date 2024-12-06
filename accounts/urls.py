from django.urls import path
from movieinfo.views import ReviewReportManagementAPIView #리뷰신고는 movieinfo/urls.py에서 지정했기 때문임
from .views import PromoteToExpertAPIView,GitFlowDiagramAPIView # 관리자 좋아요100개 지정
from .views import MovieListAPIView, MovieDetailsAPIView
from .views import CheckLoginAPIView
from .views import generate_diagram
from .views import (
    RegisterUserAPIView, 
    UserProfileView, 
    LogoutAPIView, 
    UserProfileUpdateView, 
    FollowAPIView, 
    FavoriteAPIView, 
    ReviewCreateAPIView, 
    ReviewUpdateAPIView, 
    ReviewDeleteAPIView, 
    MovieReviewsAPIView, 
    UserReviewsAPIView, 
    MovieReviewStatisticsAPIView, 
    ReviewReactionAPIView, 
    ReviewListSortedAPIView,
        CommentCreateAPIView,
    CommentListAPIView,
    CommentUpdateAPIView, 
    CommentDeleteAPIView,
    AdminControlAPIView,  # 관리자 관련 기능
    ExpertReviewAPIView,  # 전문가 리뷰 조회
    RegularReviewAPIView,  # 일반 사용자 리뷰 조회
)

urlpatterns = [
    # 회원가입 및 프로필
    path('register/', RegisterUserAPIView.as_view(), name='register'),  # 회원가입
    path('profile/', UserProfileView.as_view(), name='profile'),  # 프로필 조회
    path('profile/update/', UserProfileUpdateView.as_view(), name='profile_update'),  # 프로필 수정

     path('auth/check-login/', CheckLoginAPIView.as_view(), name='check-login'),   #로그인 확인

    # 로그아웃
    path('logout/', LogoutAPIView.as_view(), name='logout'),  # 로그아웃

    # 리뷰 관련
    path('reviews/', ReviewCreateAPIView.as_view(), name='review_create'),  # 리뷰 작성
    path('reviews/<int:review_id>/', ReviewUpdateAPIView.as_view(), name='review_update'),  # 리뷰 수정
    path('reviews/<int:review_id>/delete/', ReviewDeleteAPIView.as_view(), name='review_delete'),  # 리뷰 삭제
    path('reviews/movie/<int:movieCd>/', MovieReviewsAPIView.as_view(), name='movie_reviews'),  # 특정 영화 리뷰 조회
    path('reviews/user/', UserReviewsAPIView.as_view(), name='user_reviews'),  # 사용자 리뷰 조회
    path('reviews/statistics/<int:movieCd>/', MovieReviewStatisticsAPIView.as_view(), name='movie_review_statistics'),  # 영화 리뷰 통계
    path('reviews/sorted/', ReviewListSortedAPIView.as_view(), name='review_list_sorted'),  # 리뷰 정렬
    path('reviews/<int:review_id>/reaction/', ReviewReactionAPIView.as_view(), name='review_reaction'),  # 리뷰 좋아요/싫어요

    #리뷰 신고 관련
    path('admin/reports/',ReviewReportManagementAPIView.as_view(), name='review_reports'),  # 신고 목록 조회
    path('admin/reports/<int:report_id>/resolve/', ReviewReportManagementAPIView.as_view(), name='resolve_report'),  # 신고 처리

    # 전문가 및 일반 리뷰
    path('reviews/expert/', ExpertReviewAPIView.as_view(), name='expert_reviews'),  # 전문가 리뷰 조회
    path('reviews/general/', RegularReviewAPIView.as_view(), name='general_reviews'),  # 일반 사용자 리뷰 조회
    path('admin/promote-to-expert/', PromoteToExpertAPIView.as_view(), name='promote_to_expert'), #전문가 좋아요100개 지정

    # 관리자 관련
    path('admin/', AdminControlAPIView.as_view(), name='admin_functions'),  # 관리자 관련 엔드포인트

    #깃플로우 직관화
    path('generate-diagram/', generate_diagram, name='generate_diagram'),
    path('admin/git-flow-diagram/', GitFlowDiagramAPIView.as_view(), name='git_flow_diagram'),

    #댓글관련 
    path('reviews/<int:review_id>/comments/', CommentListAPIView.as_view(), name='comment_list'),  # 특정 리뷰의 댓글 목록
    path('reviews/<int:review_id>/comments/create/', CommentCreateAPIView.as_view(), name='comment_create'),  # 댓글 생성
    path('comments/<int:comment_id>/update/', CommentUpdateAPIView.as_view(), name='comment_update'),  # 댓글 수정
    path('comments/<int:comment_id>/delete/', CommentDeleteAPIView.as_view(), name='comment_delete'),  # 댓글 삭제


    #영화 정보 받기
    path('movies/', MovieListAPIView.as_view(), name='movie_list'),  # 영화 목록 조회
    path('movies/<int:movieCd>/', MovieDetailsAPIView.as_view(), name='movie_detail'),  # 특정 영화 정보 조회

    # 즐겨찾기
    path("favorites/", FavoriteAPIView.as_view(), name="favorites_list"),  # 즐겨찾기 목록
    path("favorites/<int:movieCd>/", FavoriteAPIView.as_view(), name="favorites_detail"),  # 특정 영화 즐겨찾기

    # 팔로우
    path('follow/<int:user_id>/', FollowAPIView.as_view(), name='follow')  # 팔로우/언팔로우

]