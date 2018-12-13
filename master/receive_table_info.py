from master_server.packages.receive import ReceiveRabbitMQMessage
from time import sleep
import json
from master_server.models import PyScriptBaseInfoV2
import traceback
from master_server.packages.mysql_check import connection_usable


class ReceiveTableInfo:
    def __init__(self, maintain_cal):
        self.maintain_cal = maintain_cal

    def events_listener(self):
        while True:
            try:
                name = "table"
                mq = ReceiveRabbitMQMessage(name=name, target=self.callback, exchange='table_events')
                mq.start()
            except Exception as e:
                sleep(1)

    def callback(self, ch, method, properties, body):
        try:
            connection_usable()
            log_str = body.decode('utf-8')
            log_dict = json.loads(log_str)
            if 'tid' in log_dict:
                tid = log_dict['tid']
            else:
                return
            p = PyScriptBaseInfoV2.objects.filter(pre_tables__pk=int(tid))
            for i in p:
                sid = str(i.pk)
                self.maintain_cal.cal_program_obj_dic[sid].table_callback(body)

        except Exception as e:
            traceback.format_exc()

        finally:
            ch.basic_ack(delivery_tag=method.delivery_tag)
