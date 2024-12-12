from django.urls import path
from .views import (
    DailyBoxOfficeAPIView, BoxOfficeBannerAPIView, MovieDetailAPIView, SimilarMoviesAPIView,
    FilterAndSortAPIView, MovieSearchAPIView, RecentMoviesAPIView, MoviesByGenreAPIView
    )

urlpatterns = [
    path('api/boxoffice/daily/', DailyBoxOfficeAPIView.as_view(), name='boxoffice'),
    path('api/boxoffice/banner/', BoxOfficeBannerAPIView.as_view(), name='boxoffice_banner'),
    path('api/movies/genre/<str:genre_name>/', MoviesByGenreAPIView.as_view(), name='movies-by-genre'),
    path('api/movies/recent/', RecentMoviesAPIView.as_view(), name='recent-movies'),
    path('api/movies/<str:movieCd>/', MovieDetailAPIView.as_view(), name='movie_detail'),
    path('api/movies/<str:movieCd>/similar/', SimilarMoviesAPIView.as_view(), name='similar-movies'),
    path('api/filter-and-sort/movies/', FilterAndSortAPIView.as_view(), name='filter-and-sort'),
    path('api/search/movies/', MovieSearchAPIView.as_view(), name='movie-search'),
]
