from django.core.management.base import BaseCommand
from tmdb.models import TmdbMovie, Plot
import requests
from bs4 import BeautifulSoup
import json
import time

# IMDb 크롤링 함수 정의
def fetch_plot_data(imdb_id):
    # Plot summary와 synopsis가 포함된 IMDb URL
    plot_url = f"https://www.imdb.com/title/{imdb_id}/plotsummary"

    # User-Agent 헤더 설정
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                      "AppleWebKit/537.36 (KHTML, like Gecko) "
                      "Chrome/87.0.4280.88 Safari/537.36"
    }

    max_retries = 3  # 최대 재시도 횟수
    for attempt in range(max_retries):
        try:
            # 페이지 요청
            response = requests.get(plot_url, headers=headers, timeout=10)

            # 상태 코드 확인
            if response.status_code == 403:
                print("403 Forbidden: IMDb에서 접근이 차단되었습니다.")
                return None, None
            elif response.status_code != 200:
                print(f"요청 실패: 상태 코드 {response.status_code}")
                return None, None

            # BeautifulSoup 파싱
            soup = BeautifulSoup(response.text, 'html.parser')

            # Plot summary 추출
            plot_summaries = []
            summaries_section = soup.find('div', {'data-testid': 'sub-section-summaries'})
            if summaries_section:
                summary_items = summaries_section.find_all('li', {'class': 'ipc-metadata-list__item'})
                for item in summary_items:
                    summary_text = item.get_text(separator=" ", strip=True)
                    plot_summaries.append(summary_text)

            # Plot synopsis 추출
            plot_synopsis = ""
            synopsis_section = soup.find('div', {'data-testid': 'sub-section-synopsis'})
            if synopsis_section:
                synopsis_item = synopsis_section.find('li', {'class': 'ipc-metadata-list__item'})
                if synopsis_item:
                    plot_synopsis = synopsis_item.get_text(separator=" ", strip=True)

            return plot_summaries, plot_synopsis

        except requests.exceptions.RequestException as e:
            print(f"시도 {attempt + 1}: IMDb 요청 실패 - {e}")
            time.sleep(2)  # 재시도 전 대기

    print("IMDb 데이터 수집 시도 실패.")
    return None, None



class Command(BaseCommand):
    help = 'TmdbMovie 모델의 imdb_id를 사용하여 IMDb에서 플롯 정보를 크롤링하고 Plot 모델에 저장합니다.'

    def handle(self, *args, **options):
        # TmdbMovie 모델에서 imdb_id가 있는 모든 객체 가져오기
        movies = TmdbMovie.objects.filter(imdb_id__isnull=False).exclude(imdb_id='')

        total_movies = movies.count()
        for index, movie in enumerate(movies, start=1):
            imdb_id = movie.imdb_id
            title = movie.title

            print(f"[{index}/{total_movies}] {title} (IMDb ID: {imdb_id})의 플롯 수집 중...")

            # 이미 해당 영화의 Plot이 존재하는지 확인
            plot_obj, created = Plot.objects.get_or_create(movie=movie)

            if not created and plot_obj.plot_summaries and plot_obj.plot_synopsis:
                print(f"이미 {title}의 플롯 정보가 존재합니다. 다음 영화로 넘어갑니다.")
                continue

            summaries, synopsis = fetch_plot_data(imdb_id)

            if summaries is None and synopsis is None:
                print(f"{title}의 플롯 정보를 가져오지 못했습니다.")
                continue

            # plot_summaries를 JSON 문자열로 변환하여 저장
            plot_obj.plot_summaries = json.dumps(summaries, ensure_ascii=False)
            plot_obj.plot_synopsis = synopsis
            plot_obj.save()

            print(f"{title}의 플롯 정보가 저장되었습니다.")

            # IMDb의 요청 제한을 피하기 위해 대기
            time.sleep(0.3)
