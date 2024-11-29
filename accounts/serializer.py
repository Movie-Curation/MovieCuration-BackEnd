from rest_framework import serializers
from django.contrib.auth.password_validation import validate_password
from .models import User, Follow, Favorite, Review, Comment, ReviewReaction, ReviewReport, Movie


class UserRegisterSerializer(serializers.ModelSerializer):
    """
    회원가입 시 사용하는 직렬화 클래스
    """
    password = serializers.CharField(write_only=True, required=True, validators=[validate_password])
    password2 = serializers.CharField(write_only=True, required=True)  # 비밀번호 확인

    class Meta:
        model = User
        fields = ('userid', 'email', 'name', 'gender', 'preference', 'nickname', 'password', 'password2')

    def validate(self, attrs):
        # 비밀번호와 확인 비밀번호가 일치하는지 검증
        if attrs['password'] != attrs['password2']:
            raise serializers.ValidationError({"password": "Passwords didn't match."})
        return attrs

    def create(self, validated_data):
        # User 생성
        user = User.objects.create(
            userid=validated_data['userid'],
            email=validated_data['email'],
            name=validated_data['name'],
            gender=validated_data['gender'],
            preference=validated_data['preference'],
            nickname=validated_data['nickname']
        )
        user.set_password(validated_data['password'])
        user.save()
        return user


class UserProfileSerializer(serializers.ModelSerializer):
    """
    사용자 프로필 직렬화 클래스
    """
    class Meta:
        model = User
        fields = ['name', 'email', 'nickname', 'preference']
        extra_kwargs = {'email': {'required': False}}


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


class FavoriteSerializer(serializers.ModelSerializer):
    """
    즐겨찾기 기능 직렬화 클래스
    """
    class Meta:
        model = Favorite
        fields = ['id', 'movie_id', 'created_at']


class MovieSerializer(serializers.ModelSerializer):
    class Meta:
        model = Movie
        fields = ['id', 'title', 'genre', 'release_year', 'director', 'description']


class ReviewStatisticsSerializer(serializers.Serializer):
    """
    리뷰 평균 별점
    """
    movie_id = serializers.IntegerField()
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
    class Meta:
        model = Review
        fields = ['id', 'user', 'movie_id', 'rating', 'comment', 'created_at', 'updated_at']
        read_only_fields = ['user', 'created_at', 'updated_at']

    def validate_rating(self, value):
        if value < 0 or value > 10:
            raise serializers.ValidationError("Rating must be between 0 and 10.")
        return value

    def create(self, validated_data):
        """
        Review 객체 생성
        """
        return Review.objects.create(**validated_data)


class ReviewReactionSerializer(serializers.ModelSerializer):
    class Meta:
        model = ReviewReaction
        fields = ['id', 'user', 'review', 'reaction', 'created_at']
        read_only_fields = ['user', 'created_at']