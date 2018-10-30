from master_server.packages.receive import ReceiveRabbitMQMessage
from master_server.packages.log_module import write_log
from master_server.models import PyScriptBaseInfoV2, TablesInfo
from master_server.table_obj_lib.table_obj import TableObj
import json
from master_server.packages.log_module import tables_listener
from datetime import datetime
from django.db import connection
from time import sleep


class MaintainTables:
    def __init__(self):
        self.logging = write_log
        self.tables_obj_dict = dict()

    # 事件监听器 如果程序执行完成，触发callback
    def start(self):
        mq = ReceiveRabbitMQMessage(name='tables_listener', target=self.callback, exchange='result_event')
        mq.start()

    def callback(self, ch, method, properties, body):
        try:
            # 确定事件为该队列信息
            log_str = body.decode('utf-8')
            tables_listener.info(log_str)
            log_dict = json.loads(log_str)
            if 'sid' in log_dict and log_dict['type'] in (2, 3, 4, 5):
                if not is_connection_usable():
                    connection.close()
                event_hash_id = log_dict['hash_id']
                sid = log_dict['sid']
                if type(sid) != int:
                    raise Exception
                if 'version' in log_dict:
                    version = log_dict['version']
                else:
                    version = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                program_obj = PyScriptBaseInfoV2.objects.get(sid=sid)
                # program_type = program_obj.program_type
                tables_obj = TablesInfo.objects.filter(father_program=program_obj)
                tables_list = [table_obj.pk for table_obj in tables_obj]
                tables_listener.info(json.dumps(tables_list))
                for tid in tables_list:
                    if tid not in self.tables_obj_dict:
                        self.tables_obj_dict[tid] = TableObj(tid)
                    self.tables_obj_dict[tid].update(sid, event_hash_id, version)
        except Exception as e:
            self.logging.error(str(e))
        finally:
            ch.basic_ack(delivery_tag=method.delivery_tag)


def is_connection_usable():
    try:
        connection.connection.ping()
    except Exception as e:
        return False
    else:
        return True





