from django.contrib import admin
from kobis.models import Movie, Director, Actor, Company, Staff

@admin.register(Movie)
class MovieAdmin(admin.ModelAdmin):
    list_display = ('movieNm', 'movieNmEn', 'prdtYear', 'genreNm', 'watchGradeNm')  # 주요 필드 표시
    search_fields = ('movieNm', 'movieNmEn', 'genreNm')  # 검색 가능 필드
    list_filter = ('prdtYear', 'watchGradeNm')  # 필터

@admin.register(Director)
class DirectorAdmin(admin.ModelAdmin):
    list_display = ('peopleNm', 'peopleNmEn', 'movie')  # 주요 필드 표시
    search_fields = ('peopleNm', 'peopleNmEn')  # 검색 가능 필드

@admin.register(Actor)
class ActorAdmin(admin.ModelAdmin):
    list_display = ('peopleNm', 'peopleNmEn', 'cast', 'movie')  # 주요 필드 표시
    search_fields = ('peopleNm', 'peopleNmEn', 'cast')  # 검색 가능 필드

@admin.register(Company)
class CompanyAdmin(admin.ModelAdmin):
    list_display = ('companyNm', 'companyPartNm', 'movie')  # 주요 필드 표시
    search_fields = ('companyNm', 'companyPartNm')  # 검색 가능 필드

@admin.register(Staff)
class StaffAdmin(admin.ModelAdmin):
    list_display = ('peopleNm', 'staffRoleNm', 'movie')  # 주요 필드 표시
    search_fields = ('peopleNm', 'staffRoleNm')  # 검색 가능 필