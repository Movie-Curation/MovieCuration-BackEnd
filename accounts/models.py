from django.db import models
from django.conf import settings
from django.contrib.auth.models import AbstractBaseUser, BaseUserManager, PermissionsMixin

from kobis.models import Movie
from tmdb.models import Genre

class UserManager(BaseUserManager):
    def create_user(self, userid, email, name, gender, genres=None, nickname=None, password=None):
        if not email:
            raise ValueError("Users must have an email address")
        if not userid:
            raise ValueError("Users must have a userid")

        user = self.model(
            userid=userid,
            email=self.normalize_email(email),
            name=name,
            gender=gender,
            nickname=nickname,
        )
        user.set_password(password)
        user.save(using=self._db)

        # ManyToManyField를 처리하기 위해 장르 추가
        if genres:
            user.genres.set(genres)  # genres는 Genre 객체의 리스트나 QuerySet이어야 함

        return user

    def create_superuser(self, userid, email, name, gender, genres=None, nickname=None, password=None):
        user = self.create_user(
            userid=userid,
            email=email,
            name=name,
            gender=gender,
            genres=genres,
            nickname=nickname,
            password=password,
        )
        user.is_admin = True
        user.is_staff = True
        user.is_superuser = True
        user.save(using=self._db)
        return user


class User(AbstractBaseUser, PermissionsMixin):
    GENDER_CHOICES = (
        ('M', 'Male'),
        ('F', 'Female'),
        ('O', 'Other'),
    )

    userid = models.CharField(max_length=50, unique=True)
    password = models.CharField(max_length=255)
    email = models.EmailField(max_length=100, unique=True)
    name = models.CharField(max_length=50)
    gender = models.CharField(max_length=1, choices=GENDER_CHOICES)
    genres = models.ManyToManyField('tmdb.Genre', related_name="users", blank=True)  # Genre 모델 연결
    nickname = models.CharField(max_length=50, unique=True)

    # 추가된 필드
    profile_image = models.ImageField(
        upload_to="profile_images/", null=True, blank=True, help_text="사용자 프로필 이미지"
    )  # 프로필 이미지 필드

    is_active = models.BooleanField(default=True)
    is_admin = models.BooleanField(default=False)
    is_staff = models.BooleanField(default=False)  # Django's built-in staff flag
    is_expert = models.BooleanField(default=False)  # 전문가 여부 추가
    is_superuser = models.BooleanField(default=False)  # Django's built-in superuser flag

    objects = UserManager()

    USERNAME_FIELD = 'userid'
    REQUIRED_FIELDS = ['email', 'name', 'gender', 'nickname']  # genres는 ManyToManyField이므로 REQUIRED_FIELDS에서 제외

    def __str__(self):
        return self.userid

    def has_perm(self, perm, obj=None):
        return True

    def has_module_perms(self, app_label):
        return True

class Review(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)  # 리뷰 작성자
    movie = models.ForeignKey(
        'kobis.Movie', on_delete=models.CASCADE, related_name='reviews',to_field='movieCd'  # 명시적으로 movieCd를 참조
    )  
    rating = models.FloatField()  # 유저 평점
    comment = models.TextField(blank=True, null=True)  # 유저 코멘트
    created_at = models.DateTimeField(auto_now_add=True)  # 생성 시간
    updated_at = models.DateTimeField(auto_now=True)  # 수정 시간
    is_expert_review = models.BooleanField(default=False, null=False)  # 기본값 없음

    def __str__(self):
        return f"Review by {self.user} on {self.movie}"


class ReviewReaction(models.Model):
    LIKE = 'like'
    DISLIKE = 'dislike'

    REACTION_CHOICES = [
        (LIKE, 'Like'),
        (DISLIKE, 'Dislike'),
    ]

    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    review = models.ForeignKey('Review', on_delete=models.CASCADE, related_name='reactions')
    reaction = models.CharField(max_length=10, choices=REACTION_CHOICES)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('user', 'review')

    def __str__(self):
        return f"{self.user.nickname} reacted {self.reaction} to Review {self.review.id}"


class ReviewReport(models.Model):                #리뷰 신고 기능
    REVIEW_REPORT_REASONS = [
        ('spam', 'Spam or misleading'),
        ('hate', 'Hate speech or abusive content'),
        ('violence', 'Violence or dangerous acts'),
        ('other', 'Other'),
    ]

    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)  # 신고한 사용자
    review = models.ForeignKey('Review', on_delete=models.CASCADE, related_name='reports')  # 신고된 리뷰
    reason = models.CharField(max_length=50, choices=REVIEW_REPORT_REASONS)  # 신고 이유
    description = models.TextField(blank=True)  # 상세 설명
    created_at = models.DateTimeField(auto_now_add=True)  # 신고 날짜
    resolved = models.BooleanField(default=False)  # 신고 처리 여부

    def __str__(self):
        return f"Report by {self.user.username} on Review {self.review.id}"
    
# class Movie(models.Model):
#     title = models.CharField(max_length=255)
#     genre = models.CharField(max_length=255)
#     release_year = models.IntegerField(null=True, blank=True) 
#     director = models.CharField(max_length=255, null=True, blank=True)  
#     description = models.TextField(null=True, blank=True)  

#     def __str__(self):
#         return self.title

class Favorite(models.Model):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="favorites"
    )
    movie = models.ForeignKey(
        'kobis.Movie',  # kobis.Movie를 참조
        on_delete=models.CASCADE,
        related_name='favorites',
        to_field='movieCd'  # movieCd를 참조
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('user', 'movie')  # user와 movie의 조합이 유일하도록 설정

    def __str__(self):
        return f"{self.user.userid} - Movie ID {self.movie.movieCd}"  # movieCd 출력
    
class Comment(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)  # 댓글 작성자
    review = models.ForeignKey('Review', on_delete=models.CASCADE, related_name='comments')  # 연결된 리뷰
    content = models.TextField()  # 댓글 내용
    created_at = models.DateTimeField(auto_now_add=True)  # 댓글 작성 시간
    updated_at = models.DateTimeField(auto_now=True)  # 댓글 수정 시간

    def __str__(self):
        return f"Comment by {self.user.username} on Review {self.review.id}"


class Follow(models.Model):
    from_user = models.ForeignKey(settings.AUTH_USER_MODEL, related_name="following", on_delete=models.CASCADE)
    to_user = models.ForeignKey(settings.AUTH_USER_MODEL, related_name="followers", on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('from_user', 'to_user')

    def __str__(self):
        return f"{self.from_user.nickname} follows {self.to_user.nickname}"
    
class TmdbMovie(models.Model):
    id = models.IntegerField(primary_key=True, help_text="TMDB 영화 ID")
    poster_url = models.URLField(null=True, blank=True, help_text="TMDB 포스터 URL")  # 포스터 URL 필드 추가
    vote_average = models.FloatField(null=True, blank=True, help_text="TMDB 영화 평점")
    genres = models.CharField(max_length=255, null=True, blank=True, help_text="TMDB 영화 장르 (콤마로 구분된 문자열)")

    def __str__(self):
        return f"TMDB Movie {self.id}"


class Movie(models.Model):
    movieCd = models.IntegerField(primary_key=True, help_text="영화 ID")
    movieNm = models.CharField(max_length=255, help_text="영화명(국문)")
    prdtYear = models.CharField(max_length=4, null=True, blank=True, help_text="제작 연도")  # 추가
    nationNm = models.CharField(max_length=50, null=True, blank=True, help_text="국가명")  # 추가
    tmdb = models.ForeignKey(
        TmdbMovie, on_delete=models.SET_NULL, null=True, blank=True, related_name="movies"
    )

    def __str__(self):
        return self.movieNm