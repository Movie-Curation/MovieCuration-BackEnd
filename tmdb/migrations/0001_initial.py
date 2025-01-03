# Generated by Django 5.1.3 on 2024-11-29 05:02

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='Genre',
            fields=[
                ('id', models.IntegerField(help_text='TMDB 장르 ID', primary_key=True, serialize=False)),
                ('name', models.CharField(help_text='장르 이름', max_length=100)),
            ],
        ),
        migrations.CreateModel(
            name='Person',
            fields=[
                ('id', models.IntegerField(help_text='TMDB 인물 ID', primary_key=True, serialize=False)),
                ('name', models.CharField(help_text='인물 이름', max_length=255)),
                ('known_for_department', models.CharField(help_text='주요 활동 부서 (예: Acting, Directing)', max_length=100)),
                ('biography', models.TextField(blank=True, help_text='인물 전기', null=True)),
                ('birthday', models.DateField(blank=True, help_text='생일', null=True)),
                ('deathday', models.DateField(blank=True, help_text='사망일', null=True)),
                ('gender', models.IntegerField(choices=[(0, 'Unknown'), (1, 'Female'), (2, 'Male')], default=0, help_text='성별 (0: 알 수 없음, 1: 여성, 2: 남성)')),
                ('homepage', models.URLField(blank=True, help_text='개인 홈페이지 URL', null=True)),
                ('profile_path', models.CharField(blank=True, help_text='인물 사진 경로', max_length=255, null=True)),
            ],
        ),
        migrations.CreateModel(
            name='ProductionCompany',
            fields=[
                ('id', models.IntegerField(help_text='TMDB 제작사 ID', primary_key=True, serialize=False)),
                ('name', models.CharField(help_text='제작사 이름', max_length=255)),
                ('logo_path', models.CharField(blank=True, help_text='제작사 로고 경로', max_length=255, null=True)),
                ('origin_country', models.CharField(blank=True, help_text='제작사 원산지 국가 코드', max_length=10, null=True)),
            ],
        ),
        migrations.CreateModel(
            name='ProductionCountry',
            fields=[
                ('iso_3166_1', models.CharField(help_text='ISO 3166-1 국가 코드', max_length=2, primary_key=True, serialize=False)),
                ('name', models.CharField(help_text='국가 이름', max_length=100)),
            ],
        ),
        migrations.CreateModel(
            name='SpokenLanguage',
            fields=[
                ('iso_639_1', models.CharField(help_text='ISO 639-1 언어 코드', max_length=2, primary_key=True, serialize=False)),
                ('name', models.CharField(help_text='언어 이름', max_length=100)),
            ],
        ),
        migrations.CreateModel(
            name='TmdbMovie',
            fields=[
                ('id', models.IntegerField(help_text='TMDB 영화 ID', primary_key=True, serialize=False)),
                ('title', models.CharField(help_text='영화 제목', max_length=255)),
                ('original_title', models.CharField(help_text='원제', max_length=255)),
                ('overview', models.TextField(blank=True, help_text='영화 개요', null=True)),
                ('release_date', models.DateField(blank=True, help_text='개봉일', null=True)),
                ('runtime', models.PositiveIntegerField(blank=True, help_text='상영 시간 (분)', null=True)),
                ('vote_average', models.FloatField(help_text='평균 투표 점수')),
                ('vote_count', models.PositiveIntegerField(help_text='투표 수')),
                ('popularity', models.FloatField(help_text='인기 지수')),
                ('poster_path', models.CharField(blank=True, help_text='포스터 이미지 경로', max_length=255, null=True)),
                ('backdrop_path', models.CharField(blank=True, help_text='배경 이미지 경로', max_length=255, null=True)),
                ('budget', models.BigIntegerField(blank=True, help_text='예산', null=True)),
                ('revenue', models.BigIntegerField(blank=True, help_text='수익', null=True)),
                ('tagline', models.CharField(blank=True, help_text='태그라인', max_length=255, null=True)),
                ('homepage', models.URLField(blank=True, help_text='영화 공식 홈페이지 URL', null=True)),
                ('imdb_id', models.CharField(blank=True, help_text='IMDb ID', max_length=20, null=True)),
                ('created_at', models.DateTimeField(auto_now_add=True, help_text='데이터 생성 시각')),
                ('updated_at', models.DateTimeField(auto_now=True, help_text='데이터 수정 시각')),
                ('genres', models.ManyToManyField(help_text='영화 장르', related_name='movies', to='tmdb.genre')),
                ('production_companies', models.ManyToManyField(help_text='제작사', related_name='movies', to='tmdb.productioncompany')),
                ('production_countries', models.ManyToManyField(help_text='제작 국가', related_name='movies', to='tmdb.productioncountry')),
                ('spoken_languages', models.ManyToManyField(help_text='사용된 언어', related_name='movies', to='tmdb.spokenlanguage')),
            ],
        ),
        migrations.CreateModel(
            name='Plot',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('plot_summaries', models.JSONField(blank=True, help_text='플롯 요약 리스트', null=True)),
                ('plot_synopsis', models.TextField(blank=True, help_text='플롯 시놉시스', null=True)),
                ('movie', models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, related_name='plot', to='tmdb.tmdbmovie')),
            ],
        ),
        migrations.CreateModel(
            name='Crew',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('department', models.CharField(help_text='부서 (예: Directing, Writing)', max_length=100)),
                ('job', models.CharField(help_text='직무 (예: Director, Screenplay)', max_length=100)),
                ('credit_id', models.CharField(help_text='크레딧 ID', max_length=100)),
                ('person', models.ForeignKey(help_text='제작진', on_delete=django.db.models.deletion.CASCADE, related_name='crew_roles', to='tmdb.person')),
                ('movie', models.ForeignKey(help_text='제작 영화', on_delete=django.db.models.deletion.CASCADE, related_name='crew', to='tmdb.tmdbmovie')),
            ],
        ),
        migrations.CreateModel(
            name='Cast',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('character', models.CharField(help_text='배역 이름', max_length=255)),
                ('credit_id', models.CharField(help_text='크레딧 ID', max_length=100)),
                ('order', models.PositiveIntegerField(help_text='출연 순서')),
                ('person', models.ForeignKey(help_text='배우', on_delete=django.db.models.deletion.CASCADE, related_name='cast_roles', to='tmdb.person')),
                ('movie', models.ForeignKey(help_text='출연 영화', on_delete=django.db.models.deletion.CASCADE, related_name='cast', to='tmdb.tmdbmovie')),
            ],
        ),
    ]
