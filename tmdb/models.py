from django.db import models


class Genre(models.Model):
    """
    영화 장르 정보를 저장하는 모델입니다.
    """
    id = models.IntegerField(primary_key=True, help_text="TMDB 장르 ID")
    name = models.CharField(max_length=100, help_text="장르 이름")

    def __str__(self):
        return self.name

class ProductionCompany(models.Model):
    """
    영화 제작사 정보를 저장하는 모델입니다.
    """
    id = models.IntegerField(primary_key=True, help_text="TMDB 제작사 ID")
    name = models.CharField(max_length=255, help_text="제작사 이름")
    logo_path = models.CharField(max_length=255, blank=True, null=True, help_text="제작사 로고 경로")
    origin_country = models.CharField(max_length=10, blank=True, null=True, help_text="제작사 원산지 국가 코드")

    def __str__(self):
        return self.name

class ProductionCountry(models.Model):
    """
    영화 제작 국가 정보를 저장하는 모델입니다.
    """
    iso_3166_1 = models.CharField(max_length=2, primary_key=True, help_text="ISO 3166-1 국가 코드")
    name = models.CharField(max_length=100, help_text="국가 이름")

    def __str__(self):
        return self.name

class SpokenLanguage(models.Model):
    """
    영화에서 사용된 언어 정보를 저장하는 모델입니다.
    """
    iso_639_1 = models.CharField(max_length=2, primary_key=True, help_text="ISO 639-1 언어 코드")
    name = models.CharField(max_length=100, help_text="언어 이름")

    def __str__(self):
        return self.name

class Person(models.Model):
    """
    영화인(배우, 감독 등) 정보를 저장하는 모델입니다.
    """
    id = models.IntegerField(primary_key=True, help_text="TMDB 인물 ID")
    name = models.CharField(max_length=255, help_text="인물 이름")
    known_for_department = models.CharField(max_length=100, help_text="주요 활동 부서 (예: Acting, Directing)")
    biography = models.TextField(blank=True, null=True, help_text="인물 전기")
    birthday = models.DateField(blank=True, null=True, help_text="생일")
    deathday = models.DateField(blank=True, null=True, help_text="사망일")
    gender = models.IntegerField(choices=[(0, 'Unknown'), (1, 'Female'), (2, 'Male')], default=0, help_text="성별 (0: 알 수 없음, 1: 여성, 2: 남성)")
    homepage = models.URLField(blank=True, null=True, help_text="개인 홈페이지 URL")
    profile_path = models.CharField(max_length=255, blank=True, null=True, help_text="인물 사진 경로")

    def __str__(self):
        return self.name
    
    @property
    def profile_url(self):
        """
        TMDB에서 제공하는 이미지 URL을 반환합니다.
        """
        if self.profile_path:
            return f"https://image.tmdb.org/t/p/w500{self.profile_path}"
        return None

class TmdbMovie(models.Model):
    """
    영화 정보를 저장하는 모델입니다.
    """
    id = models.IntegerField(primary_key=True, help_text="TMDB 영화 ID")
    title = models.CharField(max_length=255, help_text="영화 제목")
    original_title = models.CharField(max_length=255, help_text="원제")
    overview = models.TextField(blank=True, null=True, help_text="영화 개요")
    release_date = models.DateField(blank=True, null=True, help_text="개봉일")
    runtime = models.PositiveIntegerField(blank=True, null=True, help_text="상영 시간 (분)")
    vote_average = models.FloatField(help_text="평균 투표 점수")
    vote_count = models.PositiveIntegerField(help_text="투표 수")
    popularity = models.FloatField(help_text="인기 지수")
    poster_path = models.CharField(max_length=255, blank=True, null=True, help_text="포스터 이미지 경로")
    backdrop_path = models.CharField(max_length=255, blank=True, null=True, help_text="배경 이미지 경로")
    budget = models.BigIntegerField(blank=True, null=True, help_text="예산")
    revenue = models.BigIntegerField(blank=True, null=True, help_text="수익")
    tagline = models.CharField(max_length=255, blank=True, null=True, help_text="태그라인")
    homepage = models.URLField(blank=True, null=True, help_text="영화 공식 홈페이지 URL")
    imdb_id = models.CharField(max_length=20, blank=True, null=True, help_text="IMDb ID")

    genres = models.ManyToManyField(Genre, related_name='movies', help_text="영화 장르")
    production_companies = models.ManyToManyField(ProductionCompany, related_name='movies', help_text="제작사")
    production_countries = models.ManyToManyField(ProductionCountry, related_name='movies', help_text="제작 국가")
    spoken_languages = models.ManyToManyField(SpokenLanguage, related_name='movies', help_text="사용된 언어")

    created_at = models.DateTimeField(auto_now_add=True, help_text="데이터 생성 시각")
    updated_at = models.DateTimeField(auto_now=True, help_text="데이터 수정 시각")

    def __str__(self):
        return self.title

class Cast(models.Model):
    """
    영화 출연 배우 정보를 저장하는 모델입니다.
    """
    movie = models.ForeignKey(TmdbMovie, related_name='cast', on_delete=models.CASCADE, help_text="출연 영화")
    person = models.ForeignKey(Person, related_name='cast_roles', on_delete=models.CASCADE, help_text="배우")
    character = models.CharField(max_length=255, help_text="배역 이름")
    credit_id = models.CharField(max_length=100, help_text="크레딧 ID")
    order = models.PositiveIntegerField(help_text="출연 순서")

    def __str__(self):
        return f"{self.person.name} as {self.character} in {self.movie.title}"

class Crew(models.Model):
    """
    영화 제작진(감독, 작가 등) 정보를 저장하는 모델입니다.
    """
    movie = models.ForeignKey(TmdbMovie, related_name='crew', on_delete=models.CASCADE, help_text="제작 영화")
    person = models.ForeignKey(Person, related_name='crew_roles', on_delete=models.CASCADE, help_text="제작진")
    department = models.CharField(max_length=100, help_text="부서 (예: Directing, Writing)")
    job = models.CharField(max_length=100, help_text="직무 (예: Director, Screenplay)")
    credit_id = models.CharField(max_length=100, help_text="크레딧 ID")

    def __str__(self):
        return f"{self.person.name} - {self.job} in {self.movie.title}"

# class Image(models.Model):
#     """
#     영화 이미지 정보를 저장하는 모델입니다.
#     """
#     movie = models.ForeignKey(TmdbMovie, related_name='images', on_delete=models.CASCADE, help_text="영화")
#     aspect_ratio = models.FloatField(help_text="이미지 종횡비")
#     file_path = models.CharField(max_length=255, help_text="이미지 파일 경로")
#     height = models.PositiveIntegerField(help_text="이미지 높이")
#     iso_639_1 = models.CharField(max_length=2, blank=True, null=True, help_text="ISO 639-1 언어 코드")
#     vote_average = models.FloatField(help_text="투표 평균 점수")
#     vote_count = models.PositiveIntegerField(help_text="투표 수")
#     width = models.PositiveIntegerField(help_text="이미지 너비")
#     image_type = models.CharField(max_length=50, choices=[('backdrop', 'Backdrop'), ('poster', 'Poster')], help_text="이미지 유형 (Backdrop, Poster)")

#     def __str__(self):
#         return f"{self.image_type} of {self.movie.title}"

# class Keyword(models.Model):
#     """
#     영화 키워드 정보를 저장하는 모델입니다.
#     """
#     id = models.IntegerField(primary_key=True, help_text="TMDB 키워드 ID")
#     name = models.CharField(max_length=255, help_text="키워드 이름")

#     def __str__(self):
#         return self.name

# class MovieKeyword(models.Model):
#     """
#     영화와 키워드 간의 다대다 관계를 저장하는 모델입니다.
#     """
#     movie = models.ForeignKey(TmdbMovie, related_name='keywords', on_delete=models.CASCADE, help_text="영화")
#     keyword = models.ForeignKey(Keyword, related_name='movies', on_delete=models.CASCADE, help_text="키워드")

#     def __str__(self):
#         return f"{self.keyword.name} in {self.movie.title}"

# class Collection(models.Model):
#     """
#     영화 컬렉션 정보를 저장하는 모델입니다.
#     """
#     id = models.IntegerField(primary_key=True, help_text="TMDB 컬렉션 ID")
#     name = models.CharField(max_length=255, help_text="컬렉션 이름")
#     overview = models.TextField(blank=True, null=True, help_text="컬렉션 개요")
#     poster_path = models.CharField(max_length=255, blank=True, null=True, help_text="컬렉션 포스터 경로")
#     backdrop_path = models.CharField(max_length=255, blank=True, null=True, help_text="컬렉션 배경 이미지 경로")

#     def __str__(self):
#         return self.name

# class MovieCollection(models.Model):
#     """
#     영화와 컬렉션 간의 다대다 관계를 저장하는 모델입니다.
#     """
#     movie = models.ForeignKey(TmdbMovie, related_name='collections', on_delete=models.CASCADE, help_text="영화")
#     collection = models.ForeignKey(Collection, related_name='movies', on_delete=models.CASCADE, help_text="컬렉션")

#     def __str__(self):
#         return f"{self.movie.title} in {self.collection.name}"

# class MovieTranslation(models.Model):
#     """
#     영화 번역 정보를 저장하는 모델입니다.
#     """
#     movie = models.ForeignKey(TmdbMovie, related_name='translations', on_delete=models.CASCADE, help_text="영화")
#     iso_639_1 = models.CharField(max_length=2, help_text="ISO 639-1 언어 코드")
#     iso_3166_1 = models.CharField(max_length=2, help_text="ISO 3166-1 국가 코드")
#     name = models.CharField(max_length=255, help_text="번역된 이름")
#     overview = models.TextField(blank=True, null=True, help_text="번역된 개요")

#     def __str__(self):
#         return f"{self.iso_639_1} translation of {self.movie.title}"


class Plot(models.Model):
    movie = models.OneToOneField(TmdbMovie, on_delete=models.CASCADE, related_name='plot')
    plot_summaries = models.JSONField(blank=True, null=True, help_text="플롯 요약 리스트")
    plot_synopsis = models.TextField(blank=True, null=True, help_text="플롯 시놉시스")

    def __str__(self):
        return f"Plot for {self.movie.title}"