from rest_framework.views import APIView
from rest_framework.generics import ListAPIView
from rest_framework.pagination import PageNumberPagination
from rest_framework.response import Response
from rest_framework import status
from django.conf import settings
import requests
from django.utils import timezone
from datetime import datetime, timedelta
from django.core.cache import cache
from django.db.models import Q
from functools import reduce
from operator import or_, and_

from kobis.models import Movie, Director
from tmdb.models import TmdbMovie, Genre
from kobis.serializers import MovieDetailSerializer


# 프론트엔드와의 연계를 고려하면 중복되는 기능이 있을지라도 엔드포인트를 구분하여 개발하는것도 좋은 방법이다.


class DailyBoxOfficeAPIView(APIView):
    '''
    < 박스오피스 순위 로딩하는 API >
    엔드포인트 (/api/boxoffice/daily/)
    
	- 홈페이지 로딩 시 가장 먼저 호출합니다. (별도의 입력값 없음)
	- 박스오피스 movieCd 목록과 기본 데이터를 받아옵니다.
	- json형식의 박스오피스 데이터를 받아 캐시에 저장.
    '''
    def get(self, request):
        # 캐시에서 데이터 가져오기
        cached_data = cache.get('daily_box_office')
        if cached_data:
            return Response(cached_data, status=status.HTTP_200_OK)

        # KOBIS API 호출
        base_date = datetime.now() - timedelta(days=1)
        date_str = base_date.strftime('%Y%m%d')
        kobis_url = "http://www.kobis.or.kr/kobisopenapi/webservice/rest/boxoffice/searchDailyBoxOfficeList.json"
        params = {
            'key': settings.KOBIS_API_KEY,
            'targetDt': date_str
        }
        response = requests.get(kobis_url, params=params)
        
        if response.status_code == 200:
            data = response.json().get('boxOfficeResult', {}).get('dailyBoxOfficeList', [])
            # 캐시에 저장
            cache.set('daily_box_office', data, timeout=24 * 60 * 60)  # 24시간 캐싱
            return Response(data, status=status.HTTP_200_OK)
        return Response({'error': 'Failed to fetch data'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class BoxOfficeBannerAPIView(APIView):
    '''
    < 오늘의 박스오피스 순위 배너용 API >
    엔드포인트 (/api/boxoffice/banner/)
    
	- DailyBoxOfficeAPIView API의 응답을 기반으로 필요한 영화 데이터를 가져옵니다.
	- 배너에 필요한 상세 정보를 렌더링합니다.
    
    - 출력은 리스트 형태의 json파일
    - 리스트 내부에 영화정보들이 딕셔너리 형태로 들어가있음.
    - 각 딕셔너리는 'kobis', 'tmdb' 의 키를 갖고있음.
    - 영화제목: 'kobis.movieNm'
    - 제작연도: 'kobis.prdtYear'
    - 국가: 'kobis.nationNm'
    - 포스터: 'tmdb.poster_url'
    ================================================================================
    - 아직 정보가 갱신되지 않아서 출력되지 않는 영화는 이미지가 None으로 출력됩니다.
    - 그 외의 데이터는 캐시에서 가져오므로 같은 변수명을 사용해도 출력됩니다.
    - 없는 정보는 '준비 중'으로 표시됩니다.
    '''
    
    def get(self, request):
        # 캐싱된 데이터 가져오기
        box_office_data = cache.get('daily_box_office')
        if not box_office_data:
            return Response({'error': 'Box office data not available'}, status=status.HTTP_404_NOT_FOUND)

        result = []
        for movie in box_office_data[:10]:  # 상위 10개만 처리
            try:
                # Movie 객체를 가져옴
                kobis_movie = Movie.objects.get(movieCd=movie['movieCd'])
                tmdb_movie = kobis_movie.tmdb_movie
                serializer = MovieDetailSerializer({'kobis': kobis_movie, 'tmdb': tmdb_movie})
                result.append(serializer.data)
            except Movie.DoesNotExist:
                # Movie 데이터가 없을 경우 캐싱된 박스오피스 정보를 반환
                result.append({
                    'kobis': {
                        'movieCd': movie['movieCd'],
                        'movieNm': movie.get('movieNm', '준비 중'),
                        'prdtYear': movie.get('prdtYear', '준비 중'),
                        'nationNm': movie.get('nationNm', '준비 중')
                    },
                    'tmdb': {
                        'poster_url': None,
                        'message': 'DB 내부에 정보 없음'
                    }
                })

        return Response(result, status=status.HTTP_200_OK)


class MoviesByGenreAPIView(ListAPIView):
    """
    TMDB 장르를 기준으로 영화를 필터링하여 반환하는 API
    엔드포인트: /api/movies/genre/<str:genre_name>/

    - 영화제목: 'kobis.movieNm'
    - 제작연도: 'kobis.prdtYear'
    - 국가: 'kobis.nationNm'
    - 포스터: 'tmdb.poster_url'
    """
    pagination_class = PageNumberPagination

    def get_queryset(self):
        genre_name = self.kwargs.get('genre_name', None)
        if not genre_name:
            return TmdbMovie.objects.none()
        
        # 해당 장르의 TMDB 영화 필터링
        genre = Genre.objects.filter(name__iexact=genre_name).first()
        if genre:
            return TmdbMovie.objects.filter(genres=genre)
        return TmdbMovie.objects.none()

    def list(self, request, *args, **kwargs):
        queryset = self.get_queryset()
    
        # Pagination 적용
        page = self.paginate_queryset(queryset)
        if page is not None:
            result = []
            for movie in page:
                kobis_movie = movie.kobis_movie.first()  # 첫 번째 연결된 Movie 객체
                if kobis_movie:  # 연결된 kobis_movie가 있을 경우만 처리
                    result.append(
                        MovieDetailSerializer({
                            'kobis': kobis_movie,
                            'tmdb': movie
                        }).data
                    )
            return self.get_paginated_response(result)
    
        # 데이터 직렬화
        result = []
        for movie in queryset:
            kobis_movie = movie.kobis_movie.first()
            if kobis_movie:
                result.append(
                    MovieDetailSerializer({
                        'kobis': kobis_movie,
                        'tmdb': movie
                    }).data
                )
        return Response(result, status=status.HTTP_200_OK)


class MovieDetailAPIView(APIView):
    '''
    < 영화 상세정보 API>
    엔드포인트: (/api/movies/<str:movieCd>/)
    movieCd 파라미터를 받아 영화의 상세정보를 출력합니다.
    
    ### 1. 영화 기본 정보
	- 영화 제목 (한글): `kobis.movieNm`
	- 영화 제목 (영문): `kobis.movieNmEn`
	- 원제목: `tmdb.original_title`
	- 개봉 연도: `kobis.prdtYear`
	- 상영 시간: `kobis.showTm`
	- 개봉일: `kobis.openDt`
	- 제작 상태: `kobis.prdtStatNm`
	- 장르: `tmdb.genres`
	- 관람 등급: `kobis.watchGradeNm`
	- 국가: `kobis.nationNm`
	- 상영 타입: `kobis.showTypeNm`
	- 태그라인: `tmdb.tagline`
	- 평점: `tmdb.vote_average`
	- 투표 수: `tmdb.vote_count`
	- 인기도: `tmdb.popularity`

	### 2. 영화 줄거리
	- 줄거리 (한글): `tmdb.overview`

	### 3. 영화 이미지
	- 포스터 이미지 URL: `tmdb.poster_url`
	- 배경 이미지 URL: `tmdb.backdrop_url`

	### 4. 감독 및 제작 관련 정보
	- 감독: `kobis.director`
	- 제작사: `tmdb.production_companies`

	### 5. 출연진 정보
	(출연진을 반복적으로 출력할 경우)
	- 배우 이름: `tmdb.cast[].name`
	- 배우 캐릭터 이름: `tmdb.cast[].character`
	- 배우 프로필 이미지 URL: `tmdb.cast[].profile_url`

	### 추가적으로 사용할 수 있는 필드
	- 홈페이지 링크: `tmdb.homepage`
	- 제작 국가: `tmdb.production_countries`
	- 사용 언어: `tmdb.spoken_languages[].name`
    '''
    def get(self, request, movieCd):
        try:
            kobis_movie = Movie.objects.get(movieCd=movieCd)
            tmdb_movie = kobis_movie.tmdb_movie
            serializer = MovieDetailSerializer({'kobis': kobis_movie, 'tmdb': tmdb_movie})
            return Response(serializer.data, status=status.HTTP_200_OK)
        except Movie.DoesNotExist:
            return Response({'error': 'Movie not found'}, status=status.HTTP_404_NOT_FOUND)


class SimilarMoviesAPIView(APIView):
    """
    특정 영화와 장르가 겹치는 영화 목록을 반환하며 페이지네이션을 지원합니다.
    엔드포인트: 
    /api/movies/<str:movieCd>/similar/ (기본값: ?page=1)
    /api/movies/<str:movieCd>/similar/?page=1&page_size=12 (한 페이지에 출력할 갯수 조절 가능)
    """
    def get(self, request, movieCd):
        try:
            # 기준 영화 가져오기
            kobis_movie = Movie.objects.get(movieCd=movieCd)
            tmdb_movie = kobis_movie.tmdb_movie

            # TMDB 장르 추출
            tmdb_genres = [genre.name for genre in tmdb_movie.genres.all()] if tmdb_movie else []

            # 동일한 장르를 가진 영화 필터링
            if tmdb_genres:
                query = reduce(or_, [Q(genreNm__icontains=genre) for genre in tmdb_genres])
                similar_movies = Movie.objects.filter(query).exclude(movieCd=movieCd).distinct()
            else:
                similar_movies = Movie.objects.none()  # TMDB 장르가 없으면 빈 결과 반환

            # 페이지네이터 설정
            paginator = PageNumberPagination()
            paginator.page_size = request.query_params.get('page_size', 12)  # 기본값: 12
            paginated_movies = paginator.paginate_queryset(similar_movies, request)

            # 데이터 직렬화
            result = [
                MovieDetailSerializer({'kobis': movie, 'tmdb': movie.tmdb_movie}).data
                for movie in paginated_movies
            ]

            return paginator.get_paginated_response(result)
        
        except Movie.DoesNotExist:
            return Response({'error': 'Movie not found'}, status=status.HTTP_404_NOT_FOUND)


class FilterAndSortAPIView(APIView):
    """
    < 필터링 및 정렬 API >
    엔드포인트: (/api/filter-and-sort/movies/)
    클라이언트에서 전달된 데이터에 필터링과 정렬을 적용합니다.
    필터링과 정렬을 적용할 데이터는 클라이언트에서 전달받습니다. 기존 API의 결과를 클라이언트가 받고, 이를 새로운 필터링 API로 전달하여 후처리합니다.
    """
    def post(self, request):
        # 클라이언트에서 전달된 영화 데이터
        movies = request.data.get("movies", [])
        if not movies:
            return Response({"error": "No movies data provided"}, status=status.HTTP_400_BAD_REQUEST)

        # 필터링 조건
        genre_filter = request.data.get("genre")  # 필터링: 장르
        nations_filter = request.data.get("nations")  # 필터링: 제작 국가

        # 정렬 조건
        sort_option = request.data.get("sort")  # 정렬: movieNm 또는 openDt

        # 필터링 적용
        if genre_filter:
            movies = [
                movie
                for movie in movies
                if genre_filter in movie["kobis"]["genreNm"]
            ]
        if nations_filter:
            movies = [
                movie
                for movie in movies
                if nations_filter in movie["kobis"]["nationNm"]
            ]

        # 정렬 적용
        if sort_option == "movieNm":
            movies = sorted(movies, key=lambda x: x["kobis"]["movieNm"])
        elif sort_option == "openDt":
            movies = sorted(
                movies, key=lambda x: x["kobis"]["openDt"], reverse=True
            )

        # 응답
        return Response(movies, status=status.HTTP_200_OK)
    
'''
<<React쪽 필터링 호출 코드 예제>>

import React, { useState, useEffect } from "react";

const FilteredAndSortedMovies = () => {
  const [movies, setMovies] = useState([]);
  const [filteredMovies, setFilteredMovies] = useState([]);
  const [loading, setLoading] = useState(true);

  // 필터 및 정렬 상태
  const [genre, setGenre] = useState("");
  const [nations, setNations] = useState("");
  const [sortOption, setSortOption] = useState("");

  // 기존 API 호출
  useEffect(() => {
    const fetchMovies = async () => {
      try {
        const response = await fetch("/api/movies/20247693/similar/");
        const data = await response.json();
        setMovies(data.results); // 영화 목록 저장
      } catch (error) {
        console.error("Error fetching movies:", error);
      } finally {
        setLoading(false);
      }
    };

    fetchMovies();
  }, []);

  // 필터링 및 정렬 API 호출
  const applyFiltersAndSort = async () => {
    try {
      const response = await fetch("/api/movies/filter-and-sort/", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          movies,
          genre,
          nations,
          sort: sortOption,
        }),
      });
      const data = await response.json();
      setFilteredMovies(data);
    } catch (error) {
      console.error("Error applying filters and sort:", error);
    }
  };

  if (loading) return <div>Loading...</div>;

  return (
    <div>
      <h1>Filtered and Sorted Movies</h1>
      <div>
        <label>
          Filter by Genre:
          <input
            type="text"
            value={genre}
            onChange={(e) => setGenre(e.target.value)}
            placeholder="e.g., Fantasy"
          />
        </label>
        <label>
          Filter by Nation:
          <input
            type="text"
            value={nations}
            onChange={(e) => setNations(e.target.value)}
            placeholder="e.g., South Korea"
          />
        </label>
        <label>
          Sort by:
          <select
            value={sortOption}
            onChange={(e) => setSortOption(e.target.value)}
          >
            <option value="">Default</option>
            <option value="movieNm">Name</option>
            <option value="openDt">Release Date</option>
          </select>
        </label>
        <button onClick={applyFiltersAndSort}>Apply</button>
      </div>
      <ul>
        {(filteredMovies.length > 0 ? filteredMovies : movies).map((movie) => (
          <li key={movie.kobis.movieCd}>
            {movie.kobis.movieNm} ({movie.kobis.openDt})
          </li>
        ))}
      </ul>
    </div>
  );
};

export default FilteredAndSortedMovies;

'''



class MovieSearchAPIView(APIView):
    """
    < 영화 제목으로 검색하는 API >
    엔드포인트: (/api/search/movies/)
    
    - '검색창' 에 입력된 값을 쿼리로 삼아 API에 전달해야합니다.
    - 쿼리 포함된 엔드포인트 예시: /api/search/movies/?query=베놈
    """
    def get(self, request):
        query = request.query_params.get("query", "").strip()  # 검색 키워드
        limit = int(request.query_params.get("limit", 10))  # 최대 결과 개수

        if not query:
            return Response({"error": "Query parameter is required"}, status=status.HTTP_400_BAD_REQUEST)

        # 제목 검색 (부분 일치)
        movies = Movie.objects.filter(movieNm__icontains=query)[:limit]

        # 데이터 직렬화
        result = [
            MovieDetailSerializer({'kobis': movie, 'tmdb': movie.tmdb_movie}).data
            for movie in movies
        ]

        return Response(result, status=status.HTTP_200_OK)


class RecentMoviesAPIView(APIView):
    """

    최근 3일간 추가된 영화 목록을 반환하는 API 뷰입니다.

    - 영화 제목: kobis.movieNm
    - 감독: kobis.director
    - 추가된 날짜: tmdb.created_at
    """

    def get(self, request, format=None):
        try:
            seven_days_ago = timezone.now() - timedelta(days=3) # N일 내에 추가된 영화
            
            # 최근 7일간 추가된 TmdbMovie 객체들을 필터링
            tmdb_movies = TmdbMovie.objects.filter(created_at__gte=seven_days_ago).prefetch_related(
                'kobis_movie',  # 역참조 관계는 prefetch_related 사용
                'genres',
                'production_companies',
                'production_countries',
                'spoken_languages',
                'cast__person',
                'crew__person',
                'plot',
            ).order_by('-created_at')
            
            # 데이터를 'tmdb'와 'kobis' 키로 구성
            movie_list = []
            for tmdb_movie in tmdb_movies:
                kobis_movie = tmdb_movie.kobis_movie.first()  # 첫 번째 Movie 객체 가져오기
                movie_data = {
                    'tmdb': tmdb_movie,
                    'kobis': kobis_movie
                }
                movie_list.append(movie_data)
            
            # 시리얼라이즈
            serializer = MovieDetailSerializer(movie_list, many=True)
            
            return Response(serializer.data, status=status.HTTP_200_OK)
        
        except Exception as e:
            return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)