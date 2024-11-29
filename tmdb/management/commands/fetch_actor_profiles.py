# your_app/management/commands/fetch_actor_profiles.py

import requests
from django.core.management.base import BaseCommand
from django.conf import settings
from tmdb.models import Cast, Person
import os
import logging

# 로깅 설정
logger = logging.getLogger(__name__)

class Command(BaseCommand):
    help = 'TMDB API를 통해 Cast 모델의 credit_id를 사용하여 배우 프로필 이미지를 가져옵니다.'

    def handle(self, *args, **options):
        casts = Cast.objects.filter(person__profile_path__isnull=True)
        total_casts = casts.count()
        self.stdout.write(self.style.NOTICE(f'총 {total_casts}명의 배우 프로필 이미지를 가져옵니다.'))

        for index, cast in enumerate(casts, start=1):
            credit_id = cast.credit_id
            person = cast.person

            self.stdout.write(self.style.NOTICE(f'[{index}/{total_casts}] 배우: "{person.name}" (Credit ID: {credit_id})'))

            # TMDB API를 통해 배우 정보 가져오기
            actor_data = self.get_actor_profile(credit_id)

            if not actor_data:
                self.stdout.write(self.style.WARNING(f'배우 "{person.name}"의 프로필 정보를 가져오지 못했습니다.'))
                continue

            # 프로필 이미지 경로 저장
            profile_path = actor_data.get('profile_path')
            if profile_path:
                person.profile_path = profile_path
                person.save()
                self.stdout.write(self.style.SUCCESS(f'배우 "{person.name}"의 프로필 이미지가 저장되었습니다.'))
            else:
                self.stdout.write(self.style.WARNING(f'배우 "{person.name}"의 프로필 이미지가 없습니다.'))

    def get_actor_profile(self, credit_id):
        """
        TMDB API를 사용하여 credit_id를 통해 배우의 프로필 정보를 가져옵니다.
        """
        url = f"{settings.TMDB_API_BASE_URL}/credit/{credit_id}"
        headers = {
            "accept": "application/json",
            "Authorization": f"Bearer {settings.TMDB_BEARER_TOKEN}"
        }
        try:
            response = requests.get(url, headers=headers)
            response.raise_for_status()
            return response.json().get('person')
        except requests.exceptions.HTTPError as http_err:
            error_message = f'TMDB HTTP 오류 발생 (Credit ID: {credit_id}): {http_err}'
            self.stdout.write(self.style.ERROR(error_message))
            logger.error(error_message)
            return None
        except requests.exceptions.RequestException as req_err:
            error_message = f'TMDB 요청 오류 발생 (Credit ID: {credit_id}): {req_err}'
            self.stdout.write(self.style.ERROR(error_message))
            logger.error(error_message)
            return None
