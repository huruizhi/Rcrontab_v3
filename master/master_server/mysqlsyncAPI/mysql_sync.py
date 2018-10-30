from master_server.packages.receive import ReceiveRabbitMQMessage
from master_server.models import TablesInfo
from urllib import request
from master_server.packages.log_module import mysql_sync
import json
from django.db import connection
from master_server.mysqlsyncAPI.mysql_sync_mq import MysqlSyncMQ
from time import sleep
from random import random
from threading import Thread


class MysqlSync:
    def table_events_listener(self):
        mq = ReceiveRabbitMQMessage(name='manual', target=self.table_callback, exchange='table_events')
        mq.start()

    def table_callback(self, ch, method, properties, body):
        ch.basic_ack(delivery_tag=method.delivery_tag)
        try:
            if not is_connection_usable():
                connection.close()
            log_str = body.decode('utf-8')
            log_dict = json.loads(log_str)
            if 'tid' in log_dict:
                tid = log_dict['tid']
                table = TablesInfo.objects.get(pk=tid)
                hash_id = log_dict['hash_id']
                mysql_sync.info('{0}, {1}'.format(tid, table.db_server))
                if table.db_server == 'db_153':
                    db_name = table.db_name
                    table_name = table.table_name
                    thread = Thread(target=self.mysql_sync_func, args=[db_name, table_name, hash_id])
                    thread.start()
        except Exception as e:
            mysql_sync.error("{name}:{err}".format(name=__name__, err=str(e)))

    # 同步数据库，调用同步消费者
    @staticmethod
    def mysql_sync_func(db_name, table_name, hash_id):
        sleep_time = int(60*20+10*60*random())
        sleep(sleep_time)
        page = ''
        table = "{db_name}.{table_name}".format(db_name=db_name, table_name=table_name)
        sync_pai = {"table_name": table, "token": "MpaCG=xN8Q5XL0b>#SdEhcpD", "taskid": hash_id}
        header = {'Content-Type': 'application/json'}
        # url = 'http://120.27.245.74:3810/create/tasks'
        url = 'http://192.168.0.156:3810/create/tasks'
        data = json.dumps(sync_pai).encode('utf-8')
        req = request.Request(url, data=data, headers=header)

        try:
            page = request.urlopen(req).read()
            page = page.decode('utf-8')
        except Exception as e:
            page = "{page}, Mq_Err {err}".format(page=page, err=str(e))
        finally:
            mysql_sync.info(
                '{db_name}.{table_name}:{page}'.format(db_name=db_name, table_name=table_name, page=page))


def is_connection_usable():
    try:
        connection.connection.ping()
    except Exception as e:
        return False
    else:
        return True
