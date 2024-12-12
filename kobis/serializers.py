from rest_framework import serializers
from kobis.models import Movie
from tmdb.models import TmdbMovie


class MovieDetailSerializer(serializers.Serializer):
    """
    Movie와 TmdbMovie 데이터를 통합하여 상세한 정보를 제공합니다.
    """
    kobis = serializers.SerializerMethodField()
    tmdb = serializers.SerializerMethodField()

    def get_kobis(self, obj):
        if obj.get('kobis'):
            movie = obj['kobis']
            return {
                'movieCd': movie.movieCd,  # 영화 코드
                'movieNm': movie.movieNm,  # 영화명(국문)
                'movieNmEn': movie.movieNmEn,  # 영화명(영문)
                'movieNmOg': movie.movieNmOg,  # 영화명(원문)
                'prdtYear': movie.prdtYear,  # 제작년도
                'showTm': movie.showTm,  # 상영시간
                'openDt': movie.openDt,  # 개봉일
                'prdtStatNm': movie.prdtStatNm,  # 제작상태
                'genreNm': movie.genreNm,  # 장르명
                'nationNm': movie.nationNm,  # 제작 국가명
                'showTypeNm': movie.showTypeNm,  # 상영 형태
                'audits': movie.audits,  # 심의정보
                'watchGradeNm': movie.watchGradeNm,  # 관람 등급
                'director': self.get_director(movie),  # 감독 정보
            }
        return None

    def get_director(self, movie):
        """
        Movie와 연결된 Director의 peopleNm 필드를 가져옵니다.
        """
        director = movie.directors.first()  # 연결된 첫 번째 감독
        return director.peopleNm if director else None

    def get_tmdb(self, obj):
        tmdb = obj.get('tmdb')  # TMDB 영화 데이터
        if not tmdb:  # 데이터가 없는 경우 초기화시킴
            return {
                "message": "연관된 TMDB 정보가 없습니다.",
                "id": None,
                "title": None,
                "original_title": None,
                "overview": None,
                "release_date": None,
                "runtime": None,
                "vote_average": None,
                "vote_count": None,
                "popularity": None,
                "budget": None,
                "revenue": None,
                "tagline": None,
                "homepage": None,
                "poster_url": None,
                "backdrop_url": None,
                "genres": [],
                "production_companies": [],
                "production_countries": [],
                "spoken_languages": [],
                "cast": [],
                "created_at": None,
            }
        # TMDB 데이터가 있는 경우 정상 처리
        return {
            'id': tmdb.id,  # TMDB 영화 ID
            'title': tmdb.title,  # 영화 제목
            'original_title': tmdb.original_title,  # 원제
            'overview': tmdb.overview,  # 영화 개요
            'release_date': tmdb.release_date,  # 개봉일
            'runtime': tmdb.runtime,  # 상영 시간 (분)
            'vote_average': tmdb.vote_average,  # 평균 평점
            'vote_count': tmdb.vote_count,  # 투표 수
            'popularity': tmdb.popularity,  # 인기 지수
            'budget': tmdb.budget,  # 제작 예산
            'revenue': tmdb.revenue,  # 수익
            'tagline': tmdb.tagline,  # 태그라인
            'homepage': tmdb.homepage,  # 공식 홈페이지
            'poster_url': f"https://image.tmdb.org/t/p/w500{tmdb.poster_path}" if tmdb.poster_path else None,
            'backdrop_url': f"https://image.tmdb.org/t/p/w500{tmdb.backdrop_path}" if tmdb.backdrop_path else None,
            'genres': [genre.name for genre in tmdb.genres.all()],  # 장르
            'production_companies': [
                {
                    'name': company.name,
                    'logo': f"https://image.tmdb.org/t/p/w500{company.logo_path}" if company.logo_path else None,
                    'origin_country': company.origin_country,
                }
                for company in tmdb.production_companies.all()
            ],  # 제작사
            'production_countries': [
                {
                    'iso_code': country.iso_3166_1,
                    'name': country.name,
                }
                for country in tmdb.production_countries.all()
            ],  # 제작 국가
            'spoken_languages': [
                {
                    'iso_code': lang.iso_639_1,
                    'name': lang.name,
                }
                for lang in tmdb.spoken_languages.all()
            ],  # 사용 언어
            
            'cast': self.get_cast(tmdb),  # 출연 배우 정보
            'created_at': tmdb.created_at,
        }
    
    def get_cast(self, tmdb):
        """
        TMDB 데이터에서 출연 배우 정보를 가져옵니다.
        """
        return [
            {
                'name': cast.person.name,
                'character': cast.character,
                'profile_url': cast.person.profile_url,  # 프로필 사진 URL
            }
            for cast in tmdb.cast.all()
        ]

