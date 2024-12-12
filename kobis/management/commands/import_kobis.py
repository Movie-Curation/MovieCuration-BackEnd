import requests
from django.core.management.base import BaseCommand
from django.conf import settings
from kobis.models import (
    Movie, Director, Actor, Company, Staff,
)
from datetime import datetime, timedelta
import logging

# 로깅 설정
logger = logging.getLogger(__name__)

class Command(BaseCommand):
    help = 'KOBIS API를 이용하여 주별 박스오피스 데이터를 일정 범위 내에서 수집하고 데이터베이스에 저장합니다.'

    def add_arguments(self, parser):
        parser.add_argument(
            '--startDt',
            type=str,
            help='조회할 시작 날짜를 입력하세요 (예: 20230412). 필수 입력 항목입니다.',
            required=True
        )
        parser.add_argument(
            '--endDt',
            type=str,
            help='조회할 종료 날짜를 입력하세요 (예: 20230419). 필수 입력 항목입니다.',
            required=True
        )
        parser.add_argument(
            '--weekGb',
            type=str,
            choices=['0', '1', '2', '3', '4'],  # KOBIS API 문서에 따른 weekGb 옵션
            help='조회할 주 구분을 입력하세요 (0: 전체, 1: 주간, 2: 주중, 3: 주말, 4: 격주). 기본값은 0입니다.',
            default='0'
        )
        parser.add_argument(
            '--interval',
            type=int,
            help='조회할 날짜 간격을 설정합니다 (단위: 일). 기본값은 7 (주간 간격)입니다.',
            default=7
        )

    def handle(self, *args, **options):
        # 조회할 날짜 범위 설정
        start_dt_str = options.get('startDt')
        end_dt_str = options.get('endDt')
        week_gb = options.get('weekGb')
        interval = options.get('interval')

        try:
            start_dt = datetime.strptime(start_dt_str, '%Y%m%d')
            end_dt = datetime.strptime(end_dt_str, '%Y%m%d')
        except ValueError:
            self.stdout.write(self.style.ERROR('날짜 형식이 올바르지 않습니다. YYYYMMDD 형식으로 입력해주세요.'))
            return

        if start_dt > end_dt:
            self.stdout.write(self.style.ERROR('시작 날짜가 종료 날짜보다 늦습니다.'))
            return

        self.stdout.write(self.style.NOTICE(f'조회 시작 날짜: {start_dt_str}'))
        self.stdout.write(self.style.NOTICE(f'조회 종료 날짜: {end_dt_str}'))
        self.stdout.write(self.style.NOTICE(f'주 구분: {week_gb}'))
        self.stdout.write(self.style.NOTICE(f'날짜 간격: {interval}일'))

        current_dt = start_dt

        while current_dt <= end_dt:
            target_dt_str = current_dt.strftime('%Y%m%d')
            self.stdout.write(self.style.NOTICE(f'[{target_dt_str}] 박스오피스 데이터 수집을 시작합니다.'))

            try:
                # 박스오피스 목록 가져오기
                boxoffice_list = self.get_weekly_boxoffice_list(target_dt_str, week_gb)
                if not boxoffice_list:
                    self.stdout.write(self.style.WARNING(f'[{target_dt_str}] 검색된 박스오피스 데이터가 없습니다.'))
                else:
                    for boxoffice in boxoffice_list:
                        movieCd = boxoffice.get('movieCd')
                        self.stdout.write(self.style.NOTICE(f'영화 코드 {movieCd}에 대한 상세 정보를 가져옵니다.'))
                        movie_detail = self.get_kobis_movie_detail(movieCd)
                        if movie_detail:
                            self.save_movie_data(movie_detail)
            except Exception as e:
                error_message = f'[{target_dt_str}] 오류 발생: {e}'
                self.stdout.write(self.style.ERROR(error_message))
                logger.error(error_message)

            # 다음 날짜로 이동
            current_dt += timedelta(days=interval)

        self.stdout.write(self.style.SUCCESS('주별 박스오피스 데이터 수집이 완료되었습니다.'))

    def get_weekly_boxoffice_list(self, targetDt, weekGb):
        """
        KOBIS API를 이용하여 주별 박스오피스 목록을 검색합니다.
        """
        url = f"{settings.KOBIS_API_BASE_URL}/boxoffice/searchWeeklyBoxOfficeList.json"
        params = {
            'key': settings.KOBIS_API_KEY,
            'targetDt': targetDt,
            'weekGb': weekGb
        }
        try:
            response = requests.get(url, params=params)
            response.raise_for_status()
            data = response.json()
            boxoffice_list = data.get('boxOfficeResult', {}).get('weeklyBoxOfficeList', [])
            return boxoffice_list
        except requests.exceptions.RequestException as req_err:
            error_message = f'박스오피스 목록 조회 실패: {req_err}'
            self.stdout.write(self.style.ERROR(error_message))
            logger.error(error_message)
            return []

    def get_kobis_movie_detail(self, movieCd):
        """
        KOBIS API를 이용하여 특정 영화의 상세 정보를 가져옵니다.
        """
        url = f"{settings.KOBIS_API_BASE_URL}/movie/searchMovieInfo.json"
        params = {
            'key': settings.KOBIS_API_KEY,
            'movieCd': movieCd
        }
        try:
            response = requests.get(url, params=params)
            response.raise_for_status()
            data = response.json()
            movie_info = data.get('movieInfoResult', {}).get('movieInfo', {})
            return movie_info
        except requests.exceptions.RequestException as req_err:
            error_message = f'영화 상세 정보 조회 실패 (movieCd: {movieCd}): {req_err}'
            self.stdout.write(self.style.ERROR(error_message))
            logger.error(error_message)
            return {}

    def get_company_info(self, companyCd):
        """
        KOBIS API를 이용하여 영화사의 상세 정보를 가져옵니다.
        """
        url = f"{settings.KOBIS_API_BASE_URL}/company/searchCompanyInfo.json"
        params = {
            'key': settings.KOBIS_API_KEY,
            'companyCd': companyCd
        }
        try:
            response = requests.get(url, params=params)
            response.raise_for_status()
            data = response.json()
            company_info = data.get('companyInfoResult', {}).get('companyInfo', {})
            return company_info
        except requests.exceptions.RequestException as req_err:
            error_message = f'영화사 상세 정보 조회 실패 (companyCd: {companyCd}): {req_err}'
            self.stdout.write(self.style.ERROR(error_message))
            logger.error(error_message)
            return {}

    def get_people_info(self, peopleCd):
        """
        KOBIS API를 이용하여 영화인의 상세 정보를 가져옵니다.
        """
        url = f"{settings.KOBIS_API_BASE_URL}/people/searchPeopleInfo.json"
        params = {
            'key': settings.KOBIS_API_KEY,
            'peopleCd': peopleCd
        }
        try:
            response = requests.get(url, params=params)
            response.raise_for_status()
            data = response.json()
            people_info = data.get('peopleInfoResult', {}).get('peopleInfo', {})
            return people_info
        except requests.exceptions.RequestException as req_err:
            error_message = f'영화인 상세 정보 조회 실패 (peopleCd: {peopleCd}): {req_err}'
            self.stdout.write(self.style.ERROR(error_message))
            logger.error(error_message)
            return {}

    def save_movie_data(self, movie_info):
        """
        가져온 영화 상세 정보를 데이터베이스에 저장합니다.
        """
        if not movie_info:
            return

        # 영화 기본 정보 추출
        movie_data = {
            'movieCd': movie_info.get('movieCd'),
            'movieNm': movie_info.get('movieNm'),
            'movieNmEn': movie_info.get('movieNmEn'),
            'movieNmOg': movie_info.get('movieNmOg'),
            'prdtYear': movie_info.get('prdtYear'),
            'showTm': movie_info.get('showTm'),
            'openDt': self.parse_date(movie_info.get('openDt')),
            'prdtStatNm': movie_info.get('prdtStatNm'),
            'typeNm': movie_info.get('typeNm'),
            'nations': ','.join([nation.get('nationNm') for nation in movie_info.get('nations', [])]),
            'nationNm': ','.join([nation.get('nationNm') for nation in movie_info.get('nations', [])]),
            'genreNm': ','.join([genre.get('genreNm') for genre in movie_info.get('genres', [])]),
            'showTypes': ','.join([show_type.get('showTypeGroupNm') for show_type in movie_info.get('showTypes', [])]),
            'showTypeGroupNm': ','.join([show_type.get('showTypeGroupNm') for show_type in movie_info.get('showTypes', [])]),
            'showTypeNm': ','.join([show_type.get('showTypeNm') for show_type in movie_info.get('showTypes', [])]),
            'audits': ','.join([audit.get('auditNo') for audit in movie_info.get('audits', [])]),
            'auditNo': ','.join([audit.get('auditNo') for audit in movie_info.get('audits', [])]),
            'watchGradeNm': ','.join([audit.get('watchGradeNm') for audit in movie_info.get('audits', [])]),
            # staffs 필드는 별도로 처리할 예정
        }

        # Movie 객체 생성 또는 업데이트
        movie, created = Movie.objects.update_or_create(
            movieCd=movie_data['movieCd'],
            defaults=movie_data
        )

        if created:
            self.stdout.write(self.style.SUCCESS(f'영화 "{movie.movieNm}"이(가) 생성되었습니다.'))
        else:
            self.stdout.write(self.style.SUCCESS(f'영화 "{movie.movieNm}"이(가) 업데이트되었습니다.'))

        # 감독 정보 저장
        self.save_directors(movie, movie_info.get('directors', []))

        # 배우 정보 저장
        self.save_actors(movie, movie_info.get('actors', []))

        # 영화사 정보 저장
        self.save_companies(movie, movie_info.get('companys', []))

        # # 스텝 정보 저장
        # self.save_staffs(movie, movie_info.get('staffs', []))

    def save_directors(self, movie, directors):
        """
        감독 정보를 데이터베이스에 저장합니다.
        """
        for director in directors:
            peopleNm = director.get('peopleNm')
            peopleCd = director.get('peopleCd')
            peopleNmEn = director.get('peopleNmEn')

            # 영화인 상세 정보 가져오기 (선택 사항)
            # people_info = self.get_people_info(peopleCd)

            # Director 객체 생성
            director_obj, created = Director.objects.update_or_create(
                movie=movie,
                peopleNm=peopleNm,
                defaults={
                    'peopleNmEn': peopleNmEn
                }
            )
            if created:
                self.stdout.write(self.style.SUCCESS(f'감독 "{director_obj.peopleNm}"이(가) 추가되었습니다.'))
            else:
                self.stdout.write(self.style.SUCCESS(f'감독 "{director_obj.peopleNm}"이(가) 업데이트되었습니다.'))

    def save_actors(self, movie, actors):
        """
        배우 정보를 데이터베이스에 저장합니다.
        """
        for actor in actors:
            peopleNm = actor.get('peopleNm')
            peopleCd = actor.get('peopleCd')
            peopleNmEn = actor.get('peopleNmEn')
            cast = actor.get('cast')
            castEn = actor.get('castEn')

            # 배우 상세 정보 가져오기 (선택 사항)
            # people_info = self.get_people_info(peopleCd)

            # Actor 객체 생성
            actor_obj, created = Actor.objects.update_or_create(
                movie=movie,
                peopleNm=peopleNm,
                cast=cast,
                defaults={
                    'peopleNmEn': peopleNmEn,
                    'castEn': castEn
                }
            )
            if created:
                self.stdout.write(self.style.SUCCESS(f'배우 "{actor_obj.peopleNm}"이(가) 추가되었습니다.'))
            else:
                self.stdout.write(self.style.SUCCESS(f'배우 "{actor_obj.peopleNm}"이(가) 업데이트되었습니다.'))

    def save_companies(self, movie, companies):
        """
        영화사 정보를 데이터베이스에 저장합니다.
        """
        for company in companies:
            companyNm = company.get('companyNm')
            companyCd = company.get('companyCd')
            companyNmEn = company.get('companyNmEn')
            companyPartNm = company.get('companyPartNm')

            # 영화사 상세 정보 가져오기 (선택 사항)
            # company_info = self.get_company_info(companyCd)

            # Company 객체 생성
            company_obj, created = Company.objects.update_or_create(
                movie=movie,
                companyCd=companyCd,
                defaults={
                    'companyNm': companyNm,
                    'companyNmEn': companyNmEn,
                    'companyPartNm': companyPartNm
                }
            )
            if created:
                self.stdout.write(self.style.SUCCESS(f'영화사 "{company_obj.companyNm}"이(가) 추가되었습니다.'))
            else:
                self.stdout.write(self.style.SUCCESS(f'영화사 "{company_obj.companyNm}"이(가) 업데이트되었습니다.'))

    # def save_staffs(self, movie, staffs):
    #     """
    #     스텝 정보를 데이터베이스에 저장합니다.
    #     """
    #     for staff in staffs:
    #         peopleNm = staff.get('peopleNm')
    #         peopleCd = staff.get('peopleCd')
    #         peopleNmEn = staff.get('peopleNmEn')
    #         staffRoleNm = staff.get('staffRoleNm')

    #         # 스텝 상세 정보 가져오기 (선택 사항)
    #         # people_info = self.get_people_info(peopleCd)

    #         # Staff 객체 생성
    #         staff_obj, created = Staff.objects.update_or_create(
    #             movie=movie,
    #             peopleNm=peopleNm,
    #             staffRoleNm=staffRoleNm,
    #             defaults={
    #                 'peopleNmEn': peopleNmEn
    #             }
    #         )
    #         if created:
    #             self.stdout.write(self.style.SUCCESS(f'스텝 "{staff_obj.peopleNm}"이(가) 추가되었습니다.'))
    #         else:
    #             self.stdout.write(self.style.SUCCESS(f'스텝 "{staff_obj.peopleNm}"이(가) 업데이트되었습니다.'))

    def parse_date(self, date_str):
        """
        날짜 문자열을 YYYY-MM-DD 형식으로 변환합니다.
        """
        try:
            return datetime.strptime(date_str, '%Y%m%d').strftime('%Y-%m-%d')
        except (ValueError, TypeError):
            return date_str  # 변환이 불가능한 경우 원본 문자열 반환
