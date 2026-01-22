from django.db import models


class BoardList(models.Model):
    id = models.IntegerField(primary_key=True)
    title = models.CharField(max_length=200)
    content = models.TextField()
    ERROR_TP = models.CharField(max_length=100, blank=True, null=True)
    HANDLE_TP = models.CharField(max_length=100, blank=True, null=True)
    STATUS = models.CharField(max_length=50, blank=True, null=True)
    CREATE_DATE = models.DateField(blank=True, null=True)

    class Meta:
        db_table = 'BOARD'
        managed = False  # ✅ 장고가 이 테이블을 만들거나 수정하지 않게 함

