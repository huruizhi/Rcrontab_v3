from master_server.packages.receive import ReceiveRabbitMQMessage
from master_server.packages.log_module import write_log
from master_server.models import PyScriptBaseInfoV2, TablesInfo
import json
from master_server.packages.log_module import tables_listener
from datetime import datetime
from django.db import connection
import traceback
from master_server.packages.mysql_sync_result import MysqlSyncLog


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


        except Exception:
            self.logging.error(traceback.format_exc())
        finally:
            ch.basic_ack(delivery_tag=method.delivery_tag)

    @staticmethod
    def mysql_sync_func(db_name, table_name, ):
        occur_datetime = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        if not is_connection_usable():
            connection.close()
        tables = TablesInfo.objects.filter(table_name=table_name, db_name=db_name)
        for table_info in tables:
            db_server = table_info.db_server
            db_name = table_info.db_name
            table_name = table_info.table_name
            data = {'db_server': db_server, 'table_name': table_name,
                    'db_name': db_name, 'occur_datetime': occur_datetime}
            data = json.dumps(data)
            try:
                MysqlSyncLog(data)
                mysql_sync.info("success! {data}".format(data=data))
            except Exception as e:
                mysql_sync.error("failed! {data} {err}".format(data=data, err=e))


def is_connection_usable():
    try:
        connection.connection.ping()
    except Exception:
        write_log.error(traceback.format_exc())
        return False
    else:
        return True





