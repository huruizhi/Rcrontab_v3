from mysql_sync_log.models import SyncTaskInfo
from time import sleep
from django.db.models import Max
from threading import Thread
from slave_server.packages.log_module import mysql_sync_result_reader as mr
from slave.settings import STATIC_VARIABLE
import json
from mysql_sync_log.send_sync_to_master import SendRstToMaster
from slave_server.packages.mysql_check import connection_usable

"""
循环检查数据库的log表
将log表的信息写入 RabbitMQ与 mongodb EventHub

"""


class LoopCheckMysqlSyncLog:

    def __init__(self):
        try:
            self.pk = SyncTaskInfo.objects.filter(flag=1).aggregate(Max('pk'))['pk__max']
            if not self.pk:
                self.pk = 0
        except Exception as e:
            self.pk = 0

    def _read_log(self):
        try:
            connection_usable()
            max_flag = SyncTaskInfo.objects.order_by('-pk')[0]

            max_flag_pk = max_flag.pk

            if self.pk == max_flag_pk:
                return
            if max_flag_pk-self.pk > 20:
                max_flag_pk = self.pk+20
                max_flag = SyncTaskInfo.objects.filter(pk__lte=max_flag_pk).order_by('-pk')[0]
                max_flag_pk = max_flag.pk
            mr.info("begin:{begin},end:{end}".format(begin=self.pk, end=max_flag_pk))
            max_flag.flag = 1
            max_flag.save()

            result_logs = SyncTaskInfo.objects.filter(pk__gt=self.pk).filter(pk__lte=max_flag_pk)
            self.pk = max_flag_pk

            if result_logs:
                for r in result_logs:
                    pk = r.taskid
                    co = CheckTableObj(pk)
                    thread = Thread(target=co.check_result)
                    thread.start()
        except Exception as e:
            print(str(__name__) + ".LoopReadResultLog._read_log:\n")
            print(e)

    def loop_read_log(self):
        while True:
            self._read_log()
            sleep(20)


class CheckTableObj:
    """
    检查数据库是否同步成功
    """
    def __init__(self, pk):
        self.db_server = STATIC_VARIABLE['DB_SERVER']
        self.r_pk = pk

    def check_result(self):
        try:
            count = 0
            while True:
                r = SyncTaskInfo.objects.get(taskid=self.r_pk)
                table_name = r.tablename
                db, table = table_name.split('.')
                table_status = r.status
                mr.info('{0}, {1}'.format(self.r_pk, table_status))
                if table_status == 0 or count > 60:
                    break
                else:
                    count = count+1
                    sleep(30)

            occur_datetime = r.start_date  # 数据库中start_date为字符串类型
            data = {'db_server': self.db_server, 'table_name': table,
                    'db_name': db, 'occur_datetime': occur_datetime}
            data = json.dumps(data)
            mr.info(data)
            send_msg = SendRstToMaster(data)
            send_msg.send_msg()
            mr.info("{0} done".format(self.r_pk))
        except Exception as e:
            mr.error(str(e))


