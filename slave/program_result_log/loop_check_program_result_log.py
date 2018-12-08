from program_result_log.models import PyScriptResultLog as ResultLog
from datetime import datetime
from slave_server.packages.mysql_check import connection_usable
from slave_server.packages.log_module import result_reader
from django.db.models import Max
from time import sleep
import json
from program_result_log.send_result_to_master import SendRstToMaster
import traceback
"""
循环检查数据库的log表
将log表的信息写入 RabbitMQ与 mongodb EventHub

"""


class LoopReadResultLog:

    def __init__(self):
        try:
            connection_usable()
            self.pk = ResultLog.objects.filter(flag=1).aggregate(Max('pk'))['pk__max']
            if not self.pk:
                self.pk = 0
        except Exception as e:
            self.pk = 0

    def _read_log(self):
        connection_usable()
        try:
            max_flag = ResultLog.objects.order_by('-pk')[0]
        except Exception as e:
            return 'Table is empty'

        max_flag_pk = max_flag.pk
        if self.pk == max_flag_pk:
            return True

        if max_flag_pk-self.pk > 20:
            max_flag_pk = self.pk+20
            connection_usable()
            max_flag = ResultLog.objects.filter(pk__lte=max_flag_pk).order_by('-pk')[0]
        result_reader.info("begin:{begin},end:{end}".format(begin=self.pk, end=max_flag.pk))

        if self.pk >= max_flag.pk:
            self.pk = self.pk + 19
            return

        max_flag_pk = max_flag.pk
        max_flag.flag = 1
        max_flag.save()

        connection_usable()
        result_logs = ResultLog.objects.filter(pk__gt=self.pk).filter(pk__lte=max_flag_pk)
        self.pk = max_flag_pk
        result_reader.info("{id}".format(id=self.pk))

        for r in result_logs:
            if r.subversion:
                datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                version = r.version.strftime('%Y-%m-%d %H:%M:%S')
                subversion = r.subversion.strftime('%Y-%m-%d %H:%M:%S') if r.subversion else version
                occur_datetime = r.event_time.strftime('%Y-%m-%d %H:%M:%S')

                source = "Mysql_ResultLog_PK:{pk}".format(pk=r.pk)
                event_info = {'sid': r.script, 'type': r.event_type, 'info': r.extra_info, 'version': version,
                              'subversion': subversion, 'occur_datetime': occur_datetime, 'source': source}
                event_info = json.dumps(event_info)
                send_msg = SendRstToMaster(event_info)
                send_msg.send_msg()
                sleep(5)
            else:
                result_reader.error("{0} with out subversion".format(r.pk))

    def loop_read_log(self):
        while True:
            try:
                self._read_log()
            except Exception:
                result_reader.error(__name__ + traceback.format_exc())
            finally:
                sleep(20)
