# your_app/management/commands/import_all_data.py

from django.core.management.base import BaseCommand
from kobis.models import Movie
from tmdb.models import TmdbMovie, Plot, Person
from tmdb.management.commands.fetch_actor_profiles import Command as FetchActorProfilesCommand
from tmdb.management.commands.fetch_imdb_plots import Command as FetchIMDbPlotsCommand
from tmdb.management.commands.import_tmdb_movie_details import Command as ImportTMDBDetailsCommand
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
        tmdb_command = ImportTMDBDetailsCommand()
        try:
            if movie.tmdb_movie:
                self.stdout.write(self.style.WARNING(f"{movie.movieNm}의 TMDB 데이터가 이미 존재합니다. 스킵합니다."))
            else:
                tmdb_command.handle(movie)
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
