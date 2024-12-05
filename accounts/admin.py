from django.contrib import admin
from .models import Favorite
from kobis.models import Movie

@admin.register(Favorite)
class FavoriteAdmin(admin.ModelAdmin):
    list_display = ('id', 'user', 'get_movie_cd', 'created_at')

    def get_movie_cd(self, obj):
        return obj.movie.movieCd
    get_movie_cd.short_description = 'Movie Code'

# @admin.register(Movie)
# class MovieAdmin(admin.ModelAdmin):
#     list_display = ('title', 'genre', 'release_year', 'director')
#     search_fields = ('title', 'genre', 'director')