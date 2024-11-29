from django.contrib import admin
from tmdb.models import TmdbMovie, Genre, ProductionCompany, ProductionCountry, SpokenLanguage, Cast, Crew, Person, Plot

@admin.register(TmdbMovie)
class TmdbMovieAdmin(admin.ModelAdmin):
    list_display = ('title', 'release_date', 'vote_average', 'popularity', 'budget', 'revenue')  # 주요 필드 표시
    search_fields = ('title', 'original_title', 'tagline')  # 검색 가능 필드
    list_filter = ('release_date', 'vote_average')  # 필터

@admin.register(Genre)
class GenreAdmin(admin.ModelAdmin):
    list_display = ('id', 'name')  # 주요 필드 표시
    search_fields = ('name',)  # 검색 가능 필드

@admin.register(ProductionCompany)
class ProductionCompanyAdmin(admin.ModelAdmin):
    list_display = ('id', 'name', 'origin_country')  # 주요 필드 표시
    search_fields = ('name', 'origin_country')  # 검색 가능 필드

@admin.register(ProductionCountry)
class ProductionCountryAdmin(admin.ModelAdmin):
    list_display = ('iso_3166_1', 'name')  # 주요 필드 표시
    search_fields = ('name',)  # 검색 가능 필드

@admin.register(SpokenLanguage)
class SpokenLanguageAdmin(admin.ModelAdmin):
    list_display = ('iso_639_1', 'name')  # 주요 필드 표시
    search_fields = ('name',)  # 검색 가능 필드

@admin.register(Cast)
class CastAdmin(admin.ModelAdmin):
    list_display = ('person', 'movie', 'character', 'order')  # 주요 필드 표시
    search_fields = ('person__name', 'character', 'movie__title')  # 관계 검색

@admin.register(Crew)
class CrewAdmin(admin.ModelAdmin):
    list_display = ('person', 'movie', 'department', 'job')  # 주요 필드 표시
    search_fields = ('person__name', 'job', 'movie__title')  # 관계 검색

@admin.register(Person)
class PersonAdmin(admin.ModelAdmin):
    list_display = ('name', 'known_for_department', 'gender', 'birthday', 'deathday')  # 주요 필드 표시
    search_fields = ('name', 'biography')  # 검색 가능 필드

@admin.register(Plot)
class PlotAdmin(admin.ModelAdmin):
    list_display = ('movie',)  # 주요 필드 표시
    search_fields = ('movie__title', 'plot_synopsis')  # 관계 검색
