# Generated by Django 5.1.3 on 2024-12-09 02:43

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('accounts', '0006_alter_user_profile_image'),
    ]

    operations = [
        migrations.AddField(
            model_name='movie',
            name='nationNm',
            field=models.CharField(blank=True, help_text='국가명', max_length=50, null=True),
        ),
        migrations.AddField(
            model_name='movie',
            name='prdtYear',
            field=models.CharField(blank=True, help_text='제작 연도', max_length=4, null=True),
        ),
        migrations.AddField(
            model_name='tmdbmovie',
            name='poster_url',
            field=models.URLField(blank=True, help_text='TMDB 포스터 URL', null=True),
        ),
        migrations.AlterField(
            model_name='tmdbmovie',
            name='genres',
            field=models.CharField(blank=True, help_text='TMDB 영화 장르 (콤마로 구분된 문자열)', max_length=255, null=True),
        ),
        migrations.AlterField(
            model_name='tmdbmovie',
            name='vote_average',
            field=models.FloatField(blank=True, help_text='TMDB 영화 평점', null=True),
        ),
    ]