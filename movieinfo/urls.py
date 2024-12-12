from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from . import views
from rest_framework_simplejwt.views import (
    TokenObtainPairView,
    TokenRefreshView,
    TokenVerifyView,
)
from rest_framework import permissions
from drf_yasg.views import get_schema_view
from drf_yasg import openapi
from .views import FollowingListView, FollowersListView  # 팔로우 관련 뷰 import

# Swagger and Redoc 설정
schema_view = get_schema_view(
    openapi.Info(
        title="Movie Info API",
        default_version='v1',
        description="API documentation for the Movie Info project",
        terms_of_service="https://www.yourproject.com/terms/",
        contact=openapi.Contact(email="contact@yourproject.com"),
        license=openapi.License(name="Your License"),
    ),
    public=True,
    permission_classes=(permissions.AllowAny,),
)

urlpatterns = [
    path('', views.index, name='index'),  # 루트 경로 설정
    path('admin/', admin.site.urls),
    path('api/accounts/', include('accounts.urls')),  # accounts 앱의 URL 포함
    path('api/token/', TokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('api/token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    path('api/token/verify/', TokenVerifyView.as_view(), name='token_verify'),
    
    # Swagger와 Redoc 경로 설정
    path('swagger/', schema_view.with_ui('swagger', cache_timeout=0), name='schema-swagger-ui'),
    path('redoc/', schema_view.with_ui('redoc', cache_timeout=0), name='schema-redoc'),

    # 팔로우 관련 엔드포인트
    path('following/', FollowingListView.as_view(), name='following-list'),
    path('followers/', FollowersListView.as_view(), name='followers-list'),

    # kobis 앱 URL 포함
    path('movie/', include('kobis.urls')),

    # ai 앱 url 포함
    path('ai/', include('ai.urls')),
]

if settings.DEBUG:  # DEBUG 모드일 때만 활성화
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATICFILES_DIRS[0])
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)