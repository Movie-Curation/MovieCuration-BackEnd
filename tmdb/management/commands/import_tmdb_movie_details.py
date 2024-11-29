# your_app/management/commands/import_tmdb_movie_details.py

import requests
from django.core.management.base import BaseCommand
from django.conf import settings
from kobis.models import Movie
from tmdb.models import (
    TmdbMovie, Genre, SpokenLanguage, Person, Cast, Crew
)
from datetime import datetime
import logging
import time
import json

# 로깅 설정
logger = logging.getLogger(__name__)

class Command(BaseCommand):
    help = 'KOBIS 데이터베이스의 영화 영어 제목을 기반으로 TMDB API에서 상세 정보를 가져와 TMDB 모델에 저장합니다.'

    def handle(self, *args, **options):
        try:
            # 모든 KOBIS 영화 가져오기
            kobis_movies = Movie.objects.all()
            total_movies = kobis_movies.count()
            self.stdout.write(self.style.NOTICE(f'총 {total_movies}개의 KOBIS 영화 중 TMDB 정보를 가져옵니다.'))

            for index, kobis_movie in enumerate(kobis_movies, start=1):
                # 영어 제목 사용
                original_title = kobis_movie.movieNmEn
                # release_year = kobis_movie.release_date.year if kobis_movie.release_date else None

                if not original_title:
                    self.stdout.write(self.style.WARNING(f'영화 코드 {kobis_movie.movieCd}의 원제(original_title)가 없습니다. 스킵합니다.'))
                    continue

                self.stdout.write(self.style.NOTICE(f'[{index}/{total_movies}] 영화 제목: "{original_title}"에 대한 TMDB 정보를 가져옵니다.'))

                # TMDB API에서 영화 검색
                tmdb_search_result = self.search_tmdb_movie(original_title, release_year=None)

                if not tmdb_search_result:
                    self.stdout.write(self.style.WARNING(f'TMDB에서 "{original_title}"을(를) 찾을 수 없습니다.'))
                    continue

                # 가장 적합한 검색 결과 선택 (첫 번째 결과)
                tmdb_movie_data = tmdb_search_result[0]
                tmdb_movie_id = tmdb_movie_data.get('id')

                # TMDB 영화 상세 정보 가져오기
                tmdb_movie_detail = self.get_tmdb_movie_detail(tmdb_movie_id)

                if not tmdb_movie_detail:
                    self.stdout.write(self.style.WARNING(f'TMDB에서 영화 ID {tmdb_movie_id}의 상세 정보를 가져올 수 없습니다.'))
                    continue

                # TMDB 영화 데이터 저장
                tmdb_movie = self.save_tmdb_movie_data(tmdb_movie_detail)

                # KOBIS와 TMDB 영화 연결
                kobis_movie.tmdb_movie = tmdb_movie
                kobis_movie.save()

                self.stdout.write(self.style.SUCCESS(f'"{original_title}"의 TMDB 정보가 성공적으로 저장되었습니다.'))

                # API 호출 제한을 피하기 위해 잠시 대기 (예: 250ms)
                time.sleep(0.25)

            self.stdout.write(self.style.SUCCESS('모든 KOBIS 영화에 대한 TMDB 정보 수집이 완료되었습니다.'))

        except Exception as e:
            error_message = f'오류 발생: {e}'
            self.stdout.write(self.style.ERROR(error_message))
            logger.error(error_message)

    def search_tmdb_movie(self, query, release_year=None):
        """
        TMDB API를 이용하여 영화 영어 제목과 개봉 연도로 검색합니다.
        """
        url = f"{settings.TMDB_API_BASE_URL}/search/movie"
        headers = {
            "accept": "application/json",
            "Authorization": f"Bearer {settings.TMDB_BEARER_TOKEN}"
        }
        params = {
            'query': query,
            'language': 'ko-KR',        # 응답 언어 설정
            # 'region': 'KR',             # 지역 설정
            'include_adult': False      # 성인 컨텐츠 제외
        }
        if release_year:
            params['year'] = release_year

        try:
            response = requests.get(url, headers=headers, params=params)
            response.raise_for_status()
            data = response.json()
            results = data.get('results', [])
            return results
        except requests.exceptions.HTTPError as http_err:
            error_message = f'TMDB HTTP 오류 발생 (제목: {query}): {http_err}'
            self.stdout.write(self.style.ERROR(error_message))
            logger.error(error_message)
            return []
        except requests.exceptions.RequestException as req_err:
            error_message = f'TMDB 요청 오류 발생 (제목: {query}): {req_err}'
            self.stdout.write(self.style.ERROR(error_message))
            logger.error(error_message)
            return []

    def get_tmdb_movie_detail(self, movie_id):
        """
        TMDB API를 이용하여 특정 영화의 상세 정보를 가져옵니다.
        Bearer 토큰을 사용하여 인증합니다.
        """
        url = f"{settings.TMDB_API_BASE_URL}/movie/{movie_id}"
        headers = {
            "accept": "application/json",
            "Authorization": f"Bearer {settings.TMDB_BEARER_TOKEN}"
        }
        params = {
            'language': 'ko-KR',                # 응답 언어 설정
            'append_to_response': 'credits'     # 추가 정보 포함
        }
        try:
            response = requests.get(url, headers=headers, params=params)
            response.raise_for_status()
            movie_detail = response.json()
            return movie_detail
        except requests.exceptions.HTTPError as http_err:
            error_message = f'TMDB HTTP 오류 발생 (ID: {movie_id}): {http_err}'
            self.stdout.write(self.style.ERROR(error_message))
            logger.error(error_message)
            return {}
        except requests.exceptions.RequestException as req_err:
            error_message = f'TMDB 요청 오류 발생 (ID: {movie_id}): {req_err}'
            self.stdout.write(self.style.ERROR(error_message))
            logger.error(error_message)
            return {}

    def save_tmdb_movie_data(self, movie_detail):
        """
        TMDB 영화 상세 정보를 TmdbMovie 모델에 저장합니다.
        주연 배우(상위 5명)와 감독만 저장합니다.
        """
        if not movie_detail:
            return None

        tmdb_movie_id = movie_detail.get('id')
        title = movie_detail.get('title')
        original_title = movie_detail.get('original_title')
        overview = movie_detail.get('overview')
        release_date = movie_detail.get('release_date')
        runtime = movie_detail.get('runtime')
        vote_average = movie_detail.get('vote_average')
        vote_count = movie_detail.get('vote_count')
        popularity = movie_detail.get('popularity')
        poster_path = movie_detail.get('poster_path')
        backdrop_path = movie_detail.get('backdrop_path')
        budget = movie_detail.get('budget')
        revenue = movie_detail.get('revenue')
        tagline = movie_detail.get('tagline')
        homepage = movie_detail.get('homepage')
        imdb_id = movie_detail.get('imdb_id')

        # TMDB 영화 생성 또는 업데이트
        tmdb_movie, created = TmdbMovie.objects.update_or_create(
            id=tmdb_movie_id,
            defaults={
                'title': title,
                'original_title': original_title,
                'overview': overview,
                'release_date': self.parse_date(release_date),
                'runtime': runtime,
                'vote_average': vote_average,
                'vote_count': vote_count,
                'popularity': popularity,
                'poster_path': poster_path,
                'backdrop_path': backdrop_path,
                'budget': budget,
                'revenue': revenue,
                'tagline': tagline,
                'homepage': homepage,
                'imdb_id': imdb_id,
            }
        )

        if created:
            self.stdout.write(self.style.SUCCESS(f'TMDB 영화 "{title}"이(가) 생성되었습니다.'))
        else:
            self.stdout.write(self.style.SUCCESS(f'TMDB 영화 "{title}"이(가) 업데이트되었습니다.'))

        # 장르 저장 및 연결
        genres = movie_detail.get('genres', [])
        tmdb_movie.genres.clear()
        for genre in genres:
            genre_id = genre.get('id')
            genre_name = genre.get('name')
            tmdb_genre, _ = Genre.objects.get_or_create(id=genre_id, defaults={'name': genre_name})
            tmdb_movie.genres.add(tmdb_genre)

        # 제작사 및 제작국가 저장 부분 주석 처리
        """
        # 제작사 저장 및 연결
        production_companies = movie_detail.get('production_companies', [])
        for company in production_companies:
            company_id = company.get('id')
            company_name = company.get('name')
            logo_path = company.get('logo_path')
            origin_country = company.get('origin_country')
            tmdb_company, _ = ProductionCompany.objects.get_or_create(
                id=company_id,
                defaults={
                    'name': company_name,
                    'logo_path': logo_path,
                    'origin_country': origin_country
                }
            )
            tmdb_movie.production_companies.add(tmdb_company)

        # 제작 국가 저장 및 연결
        production_countries = movie_detail.get('production_countries', [])
        for country in production_countries:
            iso_3166_1 = country.get('iso_3166_1')
            name = country.get('name')
            tmdb_country, _ = ProductionCountry.objects.get_or_create(
                iso_3166_1=iso_3166_1,
                defaults={'name': name}
            )
            tmdb_movie.production_countries.add(tmdb_country)
        """

        # 사용된 언어 저장 및 연결
        spoken_languages = movie_detail.get('spoken_languages', [])
        tmdb_movie.spoken_languages.clear()
        for language in spoken_languages:
            iso_639_1 = language.get('iso_639_1')
            name = language.get('name')
            tmdb_language, _ = SpokenLanguage.objects.get_or_create(
                iso_639_1=iso_639_1,
                defaults={'name': name}
            )
            tmdb_movie.spoken_languages.add(tmdb_language)

        # 크레딧 정보 저장 (주연 배우 및 감독)
        credits = movie_detail.get('credits', {})
        cast_list = credits.get('cast', [])
        crew_list = credits.get('crew', [])

        # 기존 Cast 및 Crew 삭제
        tmdb_movie.cast.all().delete()
        tmdb_movie.crew.all().delete()

        # 출연진 저장 (주연 배우만)
        # 일반적으로 'order'가 낮을수록 주연 배우에 가깝다고 간주
        top_cast = sorted(cast_list, key=lambda x: x.get('order', 999))[:5]  # 상위 5명
        for cast in top_cast:
            person_id = cast.get('id')
            person_name = cast.get('name')
            known_for_department = cast.get('known_for_department')
            character = cast.get('character')
            credit_id = cast.get('credit_id')
            order = cast.get('order')

            person, _ = Person.objects.update_or_create(
                id=person_id,
                defaults={
                    'name': person_name,
                    'known_for_department': known_for_department,
                    'biography': '',  # 추가 정보 필요 시 업데이트
                    'birthday': None,  # 추가 정보 필요 시 업데이트
                    'gender': 0  # 추가 정보 필요 시 업데이트
                }
            )

            Cast.objects.create(
                movie=tmdb_movie,
                person=person,
                character=character,
                credit_id=credit_id,
                order=order
            )

        # 감독 저장
        # 크루 리스트에서 'job'이 'Director'인 사람만 저장
        directors = [crew for crew in crew_list if crew.get('job') == 'Director']
        for director in directors:
            person_id = director.get('id')
            person_name = director.get('name')
            known_for_department = director.get('known_for_department')
            department = director.get('department')
            job = director.get('job')
            credit_id = director.get('credit_id')

            person, _ = Person.objects.update_or_create(
                id=person_id,
                defaults={
                    'name': person_name,
                    'known_for_department': known_for_department,
                    'biography': '',  # 추가 정보 필요 시 업데이트
                    'birthday': None,  # 추가 정보 필요 시 업데이트
                    'gender': 0  # 추가 정보 필요 시 업데이트
                }
            )

            Crew.objects.create(
                movie=tmdb_movie,
                person=person,
                department=department,
                job=job,
                credit_id=credit_id
            )

        return tmdb_movie

    def parse_date(self, date_str):
        """
        날짜 문자열을 YYYY-MM-DD 형식으로 변환합니다.
        """
        try:
            return datetime.strptime(date_str, '%Y-%m-%d').date()
        except (ValueError, TypeError):
            return None
