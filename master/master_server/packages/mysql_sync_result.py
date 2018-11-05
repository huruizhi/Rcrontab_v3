from master_server.mongo_models import EventsHub, TableVersionTree, TableInfo
from master_server.models import TablesInfo
from master_server.packages.hash import get_hash
from master_server.packages.log_module import mysql_sync_result_reader as mr
from datetime import datetime
from master_server.collect_info_to_mq import SendProgramStatus
import json

"""
将log表的信息写入 RabbitMQ与 mongodb EventHub

"""


class MysqlSyncLog:
    def __init__(self, msg):
        msg = json.loads(msg)
        self._table_info(**msg)

    def _table_info(self, db_server, table_name, db_name, occur_datetime):
        table_info = {'table_name': table_name, 'db_name': db_name, 'db_server': db_server}
        table = TablesInfo.objects.filter(**table_info)
        if not table:
            t = TablesInfo(**table_info)
            t.save()
            tid = t.pk
        else:
            tid = table[0].pk
        mr.info(tid)

        version = datetime.now()
        version = version.strftime('%Y-%m-%d')
        event_info = {'tid': tid, 'type': 101,
                      'info': 'table QC_success',
                      'occur_datetime': occur_datetime,
                      'version': version,
                      'source': "153-ali_sync"}
        hash_id = get_hash(event_info)
        event_info['hash_id'] = hash_id
        SendProgramStatus(message=event_info, msg_type='t').send_msg()
        event = EventsHub(**event_info)
        event.save()

    @staticmethod
    def _get_version(table, db):
        version = ''
        try:
            table_info = TablesInfo.objects.get(table_name=table, db_name=db, db_server='db_153')
            tid = table_info.pk
            table_info = TableInfo.objects.get(tid=tid)
            pointer = table_info.pointer
            t = TableVersionTree.objects.get(hash_id=pointer)
            pre_version = t.pre_version
            t = TableVersionTree.objects.get(hash_id=pre_version)
            program_list = t.program_version
            for p in program_list:
                event_hash = program_list[p]
                event = EventsHub.objects.get(hash_id=event_hash)
                pre_version = event.version
                if not version:
                    version = pre_version
                elif pre_version > version:
                    version = pre_version
        except Exception as e:
            version = datetime.now()
        finally:
            if version == '':
                version = datetime.now()
            version = version.strftime('%Y-%m-%d')
            return version




