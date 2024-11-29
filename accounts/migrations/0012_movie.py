# Generated by Django 5.1.3 on 2024-11-26 01:42

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('accounts', '0011_reviewreport'),
    ]

    operations = [
        migrations.CreateModel(
            name='Movie',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('title', models.CharField(max_length=255, unique=True)),
                ('genre', models.CharField(max_length=100)),
                ('release_date', models.DateField()),
            ],
        ),
    ]
