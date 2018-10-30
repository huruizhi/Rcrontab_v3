from django.db import models

# Create your models here.


class PyScriptResultLog(models.Model):
    version = models.DateField()
    event_time = models.DateTimeField()
    subversion = models.DateTimeField(blank=True, null=True)
    event_type = models.IntegerField()
    extra_info = models.TextField(blank=True, null=True)
    flag = models.IntegerField(blank=True, null=True)
    script = models.IntegerField(blank=True, null=True, db_column='sid')

    class Meta:
        managed = False
        db_table = 'py_script_result_log'
        app_label = "program_result_log"


