from django.contrib import admin
from . import models

# Register your models here.

admin.site.register(models.ConfigFileLog)
admin.site.register(models.Path)
admin.site.register(models.PyScriptBaseInfoV2)
admin.site.register(models.PyScriptOwnerListV2)
admin.site.register(models.ResultLog)
admin.site.register(models.ServerInfo)
admin.site.register(models.TablesInfo)
