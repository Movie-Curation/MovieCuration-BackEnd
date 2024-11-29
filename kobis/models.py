from django.db import models


class Movie(models.Model):
    movieCd = models.CharField(max_length=100, unique=True, help_text="영화 코드를 출력합니다.")
    movieNm = models.CharField(max_length=255, help_text="영화명(국문)을 출력합니다.")
    movieNmEn = models.CharField(max_length=255, blank=True, null=True, help_text="영화명(영문)을 출력합니다.")
    movieNmOg = models.CharField(max_length=255, blank=True, null=True, help_text="영화명(원문)을 출력합니다.")
    prdtYear = models.CharField(max_length=4, help_text="제작연도를 출력합니다.")
    showTm = models.CharField(max_length=10, help_text="상영시간을 출력합니다.")
    openDt = models.CharField(max_length=10, help_text="개봉연도를 출력합니다.")
    prdtStatNm = models.CharField(max_length=100, help_text="제작상태명을 출력합니다.")
    typeNm = models.CharField(max_length=100, help_text="영화유형명을 출력합니다.")
    nations = models.CharField(max_length=255, help_text="제작국가를 나타냅니다.")
    nationNm = models.CharField(max_length=255, help_text="제작국가명을 출력합니다.")
    genreNm = models.CharField(max_length=255, help_text="장르명을 출력합니다.")
    showTypes = models.CharField(max_length=100, help_text="상영형태 구분을 나타냅니다.")
    showTypeGroupNm = models.CharField(max_length=100, help_text="상영형태 구분을 출력합니다.")
    showTypeNm = models.CharField(max_length=100, help_text="상영형태명을 출력합니다.")
    audits = models.CharField(max_length=255, help_text="심의정보를 나타냅니다.")
    auditNo = models.CharField(max_length=100, help_text="심의번호를 출력합니다.")
    watchGradeNm = models.CharField(max_length=100, help_text="관람등급 명칭을 출력합니다.")
    staffs = models.CharField(max_length=255, help_text="스텝을 나타냅니다.")

    # TMDB Movie와의 관계 (선택사항)
    tmdb_movie = models.ForeignKey('tmdb.TmdbMovie', on_delete=models.SET_NULL, null=True, blank=True, related_name='kobis_movie')
    
    def __str__(self):
        return self.movieNm

class Director(models.Model):
    movie = models.ForeignKey(Movie, related_name='directors', on_delete=models.CASCADE)
    peopleNm = models.CharField(max_length=255, help_text="감독명을 출력합니다.")
    peopleNmEn = models.CharField(max_length=255, blank=True, null=True, help_text="감독명(영문)을 출력합니다.")

    def __str__(self):
        return self.peopleNm

class Actor(models.Model):
    movie = models.ForeignKey(Movie, related_name='actors', on_delete=models.CASCADE)
    peopleNm = models.CharField(max_length=255, help_text="배우명을 출력합니다.")
    peopleNmEn = models.CharField(max_length=255, blank=True, null=True, help_text="배우명(영문)을 출력합니다.")
    cast = models.CharField(max_length=255, help_text="배역명을 출력합니다.")
    castEn = models.CharField(max_length=255, blank=True, null=True, help_text="배역명(영문)을 출력합니다.")

    def __str__(self):
        return self.peopleNm

class Company(models.Model):
    movie = models.ForeignKey(Movie, related_name='companies', on_delete=models.CASCADE)
    companyCd = models.CharField(max_length=100, help_text="참여 영화사 코드를 출력합니다.")
    companyNm = models.CharField(max_length=255, help_text="참여 영화사명을 출력합니다.")
    companyNmEn = models.CharField(max_length=255, blank=True, null=True, help_text="참여 영화사명(영문)을 출력합니다.")
    companyPartNm = models.CharField(max_length=255, help_text="참여 영화사 분야명을 출력합니다.")

    def __str__(self):
        return self.companyNm

class Staff(models.Model):
    movie = models.ForeignKey(Movie, related_name='staffs_details', on_delete=models.CASCADE)
    peopleNm = models.CharField(max_length=255, help_text="스텝명을 출력합니다.")
    peopleNmEn = models.CharField(max_length=255, blank=True, null=True, help_text="스텝명(영문)을 출력합니다.")
    staffRoleNm = models.CharField(max_length=255, help_text="스텝역할명을 출력합니다.")

    def __str__(self):
        return self.peopleNm
