from django.contrib import admin
from .models import Favorite
from kobis.models import Movie

@admin.register(Favorite)
class FavoriteAdmin(admin.ModelAdmin):
    list_display = ['user', 'movie_id', 'created_at']

# @admin.register(Movie)
# class MovieAdmin(admin.ModelAdmin):
#     list_display = ('title', 'genre', 'release_year', 'director')
#     search_fields = ('title', 'genre', 'director')