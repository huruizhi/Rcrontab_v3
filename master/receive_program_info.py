from master_server.packages.receive import ReceiveRabbitMQMessage
from time import sleep
import json
from master_server.models import PyScriptBaseInfoV2
import traceback
from master_server.packages.mysql_check import connection_usable


class ReceiveProgramInfo:
    def __init__(self, maintain_cron, maintain_cal):
        self.maintain_cron = maintain_cron
        self.maintain_cal = maintain_cal

    def events_listener(self):
        while True:
            try:
                mq = ReceiveRabbitMQMessage(name='program_info', target=self.callback)
                mq.start()
            except Exception as e:
                sleep(1)

    def callback(self, ch, method, properties, body):
        try:
            log_str = body.decode('utf-8')
            log_dict = json.loads(log_str)
            # 确定事件为该队列信息
            if 'sid' in log_dict:
                sid = log_dict['sid']
            else:
                return
            connection_usable()
            p = PyScriptBaseInfoV2.objects.get(sid=sid)
            sid = str(sid)
            if p.program_type == 0:
                if sid in self.maintain_cron.cron_program_obj_dic:
                    self.maintain_cron.cron_program_obj_dic[sid].callback(body)
            if p.program_type == 1:
                if sid in self.maintain_cal.cal_program_obj_dic:
                    self.maintain_cal.cal_program_obj_dic[sid].callback(body)

        except Exception as e:
            traceback.format_exc()

        finally:
            ch.basic_ack(delivery_tag=method.delivery_tag)
