from master_server.models import ResultLog
from master_server.mongo_models import EventsHub
from datetime import datetime
from master_server.packages.hash import get_hash
import json
from master_server.packages.event_product import EventProduct
from time import sleep
from django.db.models import Max
from master_server.packages.log_module import result_reader
from master_server.packages.mysql_check import connection_usable


"""
循环检查数据库的log表
将log表的信息写入 RabbitMQ与 mongodb EventHub

"""


class LoopReadResultLog:

    def __init__(self):
        try:
            self.pk = ResultLog.objects.filter(flag=1).aggregate(Max('pk'))['pk__max']
            if not self.pk:
                self.pk = 0
        except Exception as e:
            self.pk = 0

    def _read_log(self):
        try:
            connection_usable()
            max_flag = ResultLog.objects.order_by('-pk')[0]

            max_flag_pk = max_flag.pk

            if self.pk == max_flag_pk:
                return

            if max_flag_pk-self.pk > 20:
                max_flag_pk = self.pk+20
                max_flag = ResultLog.objects.filter(pk__lte=max_flag_pk).order_by('-pk')[0]
                max_flag_pk = max_flag.pk
            result_reader.info("153 begin:{begin},end:{end}".format(begin=self.pk, end=max_flag_pk))
            max_flag.flag = 1
            max_flag.save()

            result_logs = ResultLog.objects.filter(pk__gt=self.pk).filter(pk__lte=max_flag_pk)
            self.pk = max_flag_pk

            for r in result_logs:
                if r.subversion:
                    version = r.version.strftime('%Y-%m-%d %H:%M:%S')
                    subversion = r.subversion.strftime('%Y-%m-%d %H:%M:%S') if r.subversion else version
                    occur_datetime = r.event_time.strftime('%Y-%m-%d %H:%M:%S')

                    source = "Mysql_ResultLog_PK:{pk}".format(pk=r.pk)
                    event_info = {'sid': r.script_id, 'type': r.event_type, 'info': r.extra_info, 'version': version,
                                  'subversion': subversion, 'occur_datetime': occur_datetime, 'source': source}

                    hash_id = get_hash(event_info)
                    event_info['hash_id'] = hash_id
                    event = EventsHub(**event_info)
                    event.save()

                    event_info_message = {'sid': r.script_id, 'hash_id': hash_id, 'subversion': subversion,
                                          'version': version, 'type': r.event_type, 'occur_datetime': occur_datetime}
                    message = json.dumps(event_info_message)
                    result_reader.info(message)
                    while True:
                        try:
                            event_product = EventProduct()
                            event_product.broadcast_message(message=message)
                            event_product.close()
                            break
                        except Exception:
                            sleep(1)
                else:
                    result_reader.error("{0} with out subversion".format(r.pk))
        except Exception as e:
            print(str(__name__) + ".LoopReadResultLog._read_log:\n")
            print(e)

    def loop_read_log(self):
        while True:
            self._read_log()
            sleep(20)
