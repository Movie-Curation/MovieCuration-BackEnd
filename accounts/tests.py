from django.test import TestCase
from django.urls import reverse
from rest_framework.test import APITestCase
from rest_framework import status
from rest_framework_simplejwt.tokens import RefreshToken
from .models import User

class UserRegistrationTestCase(APITestCase):
    def test_user_registration(self):
        url = reverse('register')  # 'register'는 accounts/urls.py에 설정한 이름이어야 함
        data = {
            "userid": "testuser",
            "email": "testuser@example.com",
            "name": "Test User",
            "gender": "M",
            "preference": "Sci-Fi",
            "nickname": "tester",
            "password": "testpassword123",# pwd -> password로 변경  (커스텀모델이라 고쳐야됨)
            "password2": "testpassword123"
        }
        response = self.client.post(url, data, format='json')
        print(response.data)  # 오류 내용 확인을 위해 추가
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(User.objects.count(), 1)
        self.assertEqual(User.objects.get().email, "testuser@example.com")


class UserLoginTestCase(APITestCase):
    def setUp(self):
        # 테스트용 사용자 생성
        self.user = User.objects.create_user(
            userid="testuser",
            email="testuser@example.com",
            name="Test User",
            gender="M",
            preference="Sci-Fi",
            nickname="tester",
            password="testpassword123"
        )

    def test_user_login(self):
        url = reverse('token_obtain_pair')  # JWT 토큰 생성 엔드포인트 이름
        data = {
            "userid": "testuser",
            "password": "testpassword123"
        }
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('access', response.data)
        self.assertIn('refresh', response.data)


class UserProfileTestCase(APITestCase):
    def setUp(self):
        # 프로필 조회에 사용할 사용자 생성 및 인증 토큰 설정
        self.user = User.objects.create_user(
            userid="testuser",
            email="testuser@example.com",
            name="Test User",
            gender="M",
            preference="Sci-Fi",
            nickname="tester",
            password="testpassword123"
        )
        self.url = reverse('profile')  # 'profile'은 accounts/urls.py에 설정한 이름이어야 합니다
        refresh = RefreshToken.for_user(self.user)
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {refresh.access_token}')

    def test_profile_retrieve(self):
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['userid'], "testuser")