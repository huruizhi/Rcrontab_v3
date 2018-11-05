from master_server.models import TablesInfo
from master_server.packages.log_module import mysql_sync as mysql_sync_log
import json
from django.db import connection
from datetime import datetime
from master_server.packages.mysql_sync_result import MysqlSyncLog
import traceback
from time import sleep


def mysql_sync_func(tid):
    occur_datetime = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    if not is_connection_usable():
        connection.close()
    t = TablesInfo.objects.get(pk=tid)
    table_name = t.table_name
    db_name = t.db_name
    db_server = t.db_server
    if db_server == 'db_153':

        # 直接更新 db_153
        data = {'db_server': db_server, 'table_name': table_name,
                'db_name': db_name, 'occur_datetime': occur_datetime}
        data = json.dumps(data)
        MysqlSyncLog(data)

        # 其他库延迟 10 分钟 更新
        sleep(600)
        tables = TablesInfo.objects.filter(table_name=table_name, db_name=db_name)
        for table_info in tables:
            db_server = table_info.db_server
            db_name = table_info.db_name
            table_name = table_info.table_name
            if db_server == 'db_153':
                return
            data = {'db_server': db_server, 'table_name': table_name,
                    'db_name': db_name, 'occur_datetime': occur_datetime}
            data = json.dumps(data)
            try:
                MysqlSyncLog(data)
                mysql_sync_log.info("success! {data}".format(data=data))
            except Exception:
                mysql_sync_log.error("failed! {data} {err}".format(data=data, err=traceback.format_exc()))
    else:
        data = {'db_server': db_server, 'table_name': table_name,
                'db_name': db_name, 'occur_datetime': occur_datetime}
        data = json.dumps(data)
        try:
            MysqlSyncLog(data)
            mysql_sync_log.info("success! {data}".format(data=data))
        except Exception:
            mysql_sync_log.error("failed! {data} {err}".format(data=data, err=traceback.format_exc()))


def is_connection_usable():
    try:
        connection.connection.ping()
    except Exception as e:
        return False
    else:
        return True
