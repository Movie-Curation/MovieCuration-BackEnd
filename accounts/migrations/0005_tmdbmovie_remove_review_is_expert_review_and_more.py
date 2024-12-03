# Generated by Django 5.1.3 on 2024-12-03 04:08

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('accounts', '0004_remove_user_preference_user_preference'),
        ('kobis', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='TmdbMovie',
            fields=[
                ('id', models.IntegerField(help_text='TMDB 영화 ID', primary_key=True, serialize=False)),
                ('vote_average', models.FloatField(help_text='TMDB 영화 평점')),
                ('genres', models.CharField(help_text='TMDB 영화 장르 (콤마로 구분된 문자열)', max_length=255)),
            ],
        ),
        migrations.RemoveField(
            model_name='review',
            name='is_expert_review',
        ),
        migrations.RemoveField(
            model_name='review',
            name='movie_id',
        ),
        migrations.AddField(
            model_name='review',
            name='movie',
            field=models.ForeignKey(default=0, on_delete=django.db.models.deletion.CASCADE, to='kobis.movie'),
            preserve_default=False,
        ),
        migrations.AlterField(
            model_name='review',
            name='comment',
            field=models.TextField(blank=True, null=True),
        ),
        migrations.AlterField(
            model_name='review',
            name='rating',
            field=models.FloatField(),
        ),
        migrations.CreateModel(
            name='Movie',
            fields=[
                ('id', models.IntegerField(help_text='영화 ID', primary_key=True, serialize=False)),
                ('movieNm', models.CharField(help_text='영화명(국문)', max_length=255)),
                ('tmdb', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='movies', to='accounts.tmdbmovie')),
            ],
        ),
    ]
