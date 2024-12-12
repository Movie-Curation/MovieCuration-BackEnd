# your_app/management/commands/import_all_data.py

from django.core.management.base import BaseCommand
from kobis.models import Movie
from tmdb.models import TmdbMovie, Plot, Person
from tmdb.management.commands.fetch_actor_profiles import Command as FetchActorProfilesCommand
from tmdb.management.commands.fetch_imdb_plots import Command as FetchIMDbPlotsCommand
# import_missing_tmdb_movie_details의 로직을 직접 사용하기 위해 import
from tmdb.management.commands.import_missing_tmdb_movie_details import Command as ImportMissingTMDBDetailsCommand
from .import_kobis import Command as ImportKOBISCommand
import logging

logger = logging.getLogger(__name__)

class Command(BaseCommand):
    help = 'movieCd를 입력받아 KOBIS, TMDB, IMDb, 배우 프로필 데이터를 가져옵니다.'

    def add_arguments(self, parser):
        parser.add_argument(
            '--movieCd',
            type=str,
            help='가져올 영화의 KOBIS movieCd를 입력하세요.',
            required=True
        )

    def handle(self, *args, **options):
        movieCd = options.get('movieCd')
        if not movieCd:
            self.stdout.write(self.style.ERROR("movieCd를 입력해야 합니다."))
            return

        self.stdout.write(self.style.NOTICE(f"영화 코드 {movieCd}의 데이터를 가져오기 시작합니다."))

        # Step 1: KOBIS 데이터 가져오기
        self.stdout.write(self.style.NOTICE(f"KOBIS 데이터 가져오는 중..."))
        kobis_command = ImportKOBISCommand()
        try:
            # movieCd로 영화 상세 정보를 먼저 가져옴
            movie_detail = kobis_command.get_kobis_movie_detail(movieCd)
            if not movie_detail:
                self.stdout.write(self.style.ERROR(f"KOBIS에서 {movieCd}에 해당하는 영화를 찾을 수 없습니다."))
                return
            # 영화 상세 정보를 save_movie_data에 전달
            kobis_command.save_movie_data(movie_detail)
            self.stdout.write(self.style.SUCCESS(f"KOBIS 데이터 가져오기 완료!"))
        except Exception as e:
            self.stdout.write(self.style.ERROR(f"KOBIS 데이터를 가져오는 중 오류 발생: {e}"))
            logger.error(e)
            return

        # Step 2: TMDB 데이터 가져오기
        movie = Movie.objects.filter(movieCd=movieCd).first()
        if not movie:
            self.stdout.write(self.style.ERROR(f"KOBIS에서 {movieCd}에 해당하는 영화를 찾을 수 없습니다."))
            return

        self.stdout.write(self.style.NOTICE(f"TMDB 데이터 가져오는 중..."))

        if movie.tmdb_movie:
            self.stdout.write(self.style.WARNING(f"{movie.movieNm}의 TMDB 데이터가 이미 존재합니다. 스킵합니다."))
        else:
            try:
                # import_missing_tmdb_movie_details의 로직을 사용하여 특정 영화에 대한 TMDB 데이터 가져오기
                self.fetch_tmdb_movie_details(movie)
                self.stdout.write(self.style.SUCCESS(f"TMDB 데이터 가져오기 완료!"))
            except Exception as e:
                self.stdout.write(self.style.ERROR(f"TMDB 데이터를 가져오는 중 오류 발생: {e}"))
                logger.error(e)

        # Step 3: IMDb 플롯 데이터 가져오기
        self.stdout.write(self.style.NOTICE(f"IMDb 플롯 데이터 가져오는 중..."))
        imdb_command = FetchIMDbPlotsCommand()
        try:
            tmdb_movie = movie.tmdb_movie
            if tmdb_movie and Plot.objects.filter(movie=tmdb_movie).exists():
                self.stdout.write(self.style.WARNING(f"{movie.movieNm}의 IMDb 플롯 데이터가 이미 존재합니다. 스킵합니다."))
            else:
                imdb_command.handle(tmdb_movie)
                self.stdout.write(self.style.SUCCESS(f"IMDb 플롯 데이터 가져오기 완료!"))
        except Exception as e:
            self.stdout.write(self.style.ERROR(f"IMDb 데이터를 가져오는 중 오류 발생: {e}"))
            logger.error(e)

        # Step 4: 배우 프로필 데이터 가져오기
        self.stdout.write(self.style.NOTICE(f"배우 프로필 데이터 가져오는 중..."))
        actor_command = FetchActorProfilesCommand()
        try:
            missing_profiles = Person.objects.filter(profile_path__isnull=True).exists()
            if not missing_profiles:
                self.stdout.write(self.style.WARNING(f"모든 배우 프로필이 이미 존재합니다. 스킵합니다."))
            else:
                actor_command.handle()
                self.stdout.write(self.style.SUCCESS(f"배우 프로필 데이터 가져오기 완료!"))
        except Exception as e:
            self.stdout.write(self.style.ERROR(f"배우 프로필 데이터를 가져오는 중 오류 발생: {e}"))
            logger.error(e)

        self.stdout.write(self.style.SUCCESS(f"영화 코드 {movieCd}에 대한 모든 데이터 수집 완료!"))

    def fetch_tmdb_movie_details(self, kobis_movie):
        """
        특정 KOBIS 영화에 대해 TMDB 데이터를 가져와서 저장합니다.
        """
        # import_missing_tmdb_movie_details의 Command 인스턴스 생성
        tmdb_command = ImportMissingTMDBDetailsCommand()

        # 영화의 원제 (영어 제목) 가져오기
        original_title = kobis_movie.movieNmEn

        if not original_title:
            self.stdout.write(self.style.WARNING(f'영화 코드 {kobis_movie.movieCd}의 원제(original_title)가 없습니다. 스킵합니다.'))
            return

        self.stdout.write(self.style.NOTICE(f'"{original_title}"에 대한 TMDB 정보를 가져옵니다.'))

        # TMDB API에서 영화 검색
        tmdb_search_result = tmdb_command.search_tmdb_movie(original_title, release_year=None)

        if not tmdb_search_result:
            self.stdout.write(self.style.WARNING(f'TMDB에서 "{original_title}"을(를) 찾을 수 없습니다.'))
            return

        # 가장 적합한 검색 결과 선택 (첫 번째 결과)
        tmdb_movie_data = tmdb_search_result[0]
        tmdb_movie_id = tmdb_movie_data.get('id')

        # TMDB 영화 상세 정보 가져오기
        tmdb_movie_detail = tmdb_command.get_tmdb_movie_detail(tmdb_movie_id)

        if not tmdb_movie_detail:
            self.stdout.write(self.style.WARNING(f'TMDB에서 영화 ID {tmdb_movie_id}의 상세 정보를 가져올 수 없습니다.'))
            return

        # TMDB 영화 데이터 저장
        tmdb_movie = tmdb_command.save_tmdb_movie_data(tmdb_movie_detail)

        if tmdb_movie:
            # KOBIS와 TMDB 영화 연결
            kobis_movie.tmdb_movie = tmdb_movie
            kobis_movie.save()

            self.stdout.write(self.style.SUCCESS(f'"{original_title}"의 TMDB 정보가 성공적으로 저장되었습니다.'))
        else:
            self.stdout.write(self.style.ERROR(f'"{original_title}"의 TMDB 정보 저장에 실패했습니다.'))
