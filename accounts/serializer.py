from rest_framework import serializers
from django.contrib.auth.password_validation import validate_password
from .models import User, Follow, Favorite, Review, Comment, ReviewReaction, ReviewReport
from kobis.models import Movie
from tmdb.models import Genre  # Genre 모델 임포트


class UserRegisterSerializer(serializers.ModelSerializer):
    """
    회원가입 시 사용하는 직렬화 클래스
    """
    password = serializers.CharField(write_only=True, required=True, validators=[validate_password])
    password2 = serializers.CharField(write_only=True, required=True)  # 비밀번호 확인
    genres = serializers.PrimaryKeyRelatedField(
        queryset=Genre.objects.all(),
        many=True,
        required=False,
        help_text="유저가 선호하는 장르의 ID 리스트"
    )
    profile_image = serializers.ImageField(required=False)  # 프로필 이미지를 선택적으로 설정

    class Meta:
        model = User
        fields = ('userid', 'email', 'name', 'gender', 'genres', 'nickname', 'password', 'password2','profile_image')

    def validate(self, attrs):
        # 비밀번호와 확인 비밀번호가 일치하는지 검증
        if attrs['password'] != attrs['password2']:
            raise serializers.ValidationError({"password": "Passwords didn't match."})
        return attrs

    def create(self, validated_data):
        # User 생성
        genres = validated_data.pop('genres')  # genres 필드 분리
        profile_image = validated_data.pop('profile_image', None)  # profile_image 필드 분리
        user = User.objects.create(
            userid=validated_data['userid'],
            email=validated_data['email'],
            name=validated_data['name'],
            gender=validated_data['gender'],
            nickname=validated_data['nickname'],
            profile_image=profile_image  # 프로필 이미지 설정
        )

        user.set_password(validated_data['password'])
        if profile_image:
            user.profile_image = profile_image  # 프로필 이미지 저장
        user.save()

        user.genres.set(genres)  # ManyToManyField 데이터 저장
        return user


class UserProfileSerializer(serializers.ModelSerializer):
    """
    사용자 프로필 직렬화 클래스
    """
    genres = serializers.PrimaryKeyRelatedField(
        queryset=Genre.objects.all(),
        many=True,
        help_text="유저가 선호하는 장르의 ID 리스트"
    )
    profile_image = serializers.ImageField(required=False, allow_null=True)  # 이미지 직렬화 처리

    class Meta:
        model = User
        fields = fields = ['userid', 'email', 'name', 'gender', 'nickname', 'genres', 'profile_image']
        extra_kwargs = {
            'email': {'required': True, 'read_only': False},  # 이메일 수정 가능
            'name': {'required': True},  # 이름 필수
            'nickname': {'required': True},  # 닉네임 필수
        }

class FollowSerializer(serializers.ModelSerializer):
    """
    팔로우 기능 직렬화 클래스
    """
    from_user = serializers.ReadOnlyField(source='from_user.username')
    to_user_username = serializers.ReadOnlyField(source='to_user.username')
    to_user_email = serializers.ReadOnlyField(source='to_user.email')
    to_user_nickname = serializers.ReadOnlyField(source='to_user.nickname')

    class Meta:
        model = Follow
        fields = ['from_user', 'to_user_username', 'to_user_email', 'to_user_nickname', 'created_at']


class CommentSerializer(serializers.ModelSerializer):
    user = serializers.ReadOnlyField(source='user.username')  # 읽기 전용 필드로 사용자 이름 표시

    class Meta:
        model = Comment
        fields = ['id', 'user', 'review', 'content', 'created_at', 'updated_at']  # 필드 정의
        read_only_fields = ['id', 'created_at', 'updated_at', 'user']  # 작성자와 리뷰는 읽기 전용


class FavoriteSerializer(serializers.ModelSerializer):
    """
    즐겨찾기 기능 직렬화 클래스
    """
    class Meta:
        model = Favorite
        fields = ['id', 'movieCd', 'created_at']


class MovieSerializer(serializers.ModelSerializer):
    genres = serializers.StringRelatedField(many=True)

    class Meta:
        model = Movie
        fields = ['movieCd', 'movieNm', 'vote_average', 'genres']  # movieCd 사용


class ReviewStatisticsSerializer(serializers.Serializer):
    """
    리뷰 평균 별점
    """
    movieCd = serializers.IntegerField()
    average_rating = serializers.FloatField()
    review_count = serializers.IntegerField()


class ReviewReportSerializer(serializers.ModelSerializer):
    class Meta:
        model = ReviewReport
        fields = ['id', 'user', 'review', 'reason', 'description', 'created_at', 'resolved']
        read_only_fields = ['id', 'user', 'created_at', 'resolved']  # 일부 필드는 읽기 전용


class ReviewSerializer(serializers.ModelSerializer):
    """
    리뷰 기능 직렬화 클래스
    """

    # movieCd를 movie 필드와 매핑
    movieCd = serializers.PrimaryKeyRelatedField(
        queryset=Movie.objects.all(),  # Movie 모델에서 movieCd를 조회
        source='movie'  # Review 모델의 ForeignKey 필드(movie)와 매핑
    )

    tmdb_vote_average = serializers.FloatField(
        source="movie.tmdb.vote_average",  # TMDB 데이터를 Movie 모델에서 가져오기
        read_only=True
    )
    tmdb_genres = serializers.CharField(
        source="movie.tmdb.genres",  # TMDB 데이터를 Movie 모델에서 가져오기
        read_only=True
    )

    class Meta:
        model = Review
        fields = [
            'id', 'user', 'movieCd', 'rating', 'comment', 
            'created_at', 'updated_at', 'tmdb_vote_average', 'tmdb_genres'
        ]
        read_only_fields = ['user', 'created_at', 'updated_at', 'tmdb_vote_average', 'tmdb_genres']

    def validate_rating(self, value):
        if value < 0 or value > 10:
            raise serializers.ValidationError("Rating must be between 0 and 10.")
        return value


class ReviewReactionSerializer(serializers.ModelSerializer):
    class Meta:
        model = ReviewReaction
        fields = ['id', 'user', 'review', 'reaction', 'created_at']
        read_only_fields = ['user', 'created_at']