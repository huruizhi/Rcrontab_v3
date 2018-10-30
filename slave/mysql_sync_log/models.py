from django.db import models

# Create your models here.


class SyncTaskInfo(models.Model):
    taskid = models.CharField(unique=True, max_length=50)
    tablename = models.CharField(max_length=255)
    start_date = models.CharField(max_length=20)
    stop_date = models.CharField(max_length=20)
    status = models.SmallIntegerField()
    num = models.IntegerField()
    info = models.TextField(blank=True, null=True)
    flag = models.IntegerField(blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'sync_task_info'
        app_label = "mysql_sync_log"

