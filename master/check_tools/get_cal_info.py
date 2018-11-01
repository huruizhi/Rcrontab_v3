# 查询计算程序的执行情况

import os
import django

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "master.settings")
django.setup()

from master_server.mongo_models import EventsHub, TableVersionTree, TableInfo, CalProgramInfo, CalVersionTree
from master_server.models import TablesInfo, PyScriptBaseInfoV2, Path, ServerInfo
import json
from master_server.packages.hash import get_hash
from master_server.collect_info_to_mq import SendProgramStatus
from datetime import datetime
from master_server.packages.mysql_sync_result import MysqlSyncLog


class GetCalInfo:
    def __init__(self, pk=None):
        self.all_project = list()
        self.server_pk = pk
        self.table_list = list()

    def _print_project(self):
        server = ServerInfo.objects.all()
        result_str = ""
        for s_info in server:
            if '阿里' in s_info.name or '基础算法' in s_info.name:
                self.all_project.append(s_info.pk)
                result_str = result_str + " {pk} {name} <br>\n".format(pk=s_info.pk, name=s_info.name)
        return result_str

    def _get_modules(self, re_run=False):
        programs = PyScriptBaseInfoV2.objects.filter(path__server__pk=self.server_pk).filter(program_type=1)
        result_str = ""
        for p in programs:
            result_str = result_str + "{pk}, {name}, {function} <br>\n".format(pk=p.pk, name=p.name, function=p.function)
            result = self._get_sync_miss_table(p.pk)
            if result == 'success':
                result_str = result_str + 'success <br>\n'
            else:
                result_str = result_str + json.dumps(result) + '<br> <br>\n'
                if re_run is True:
                    self._re_run_program(result)

        if re_run is True:
            self._table_success()
        return result_str

    def __call__(self, *args, **kwargs):
        if self.server_pk is None:
            result_str = self._print_project()
        else:
            result_str = self._get_modules(*args, **kwargs)
        return result_str


    @staticmethod
    def _get_sync_miss_table(sid):
        p = CalProgramInfo.objects.get(sid=sid)
        p_v = CalVersionTree.objects.get(hash_id=p.pointer)
        if p_v.pre_version == 'init':
            p_v_info = json.loads(p_v.to_json())
            return p_v_info
        else:
            try:
                p_p_v = EventsHub.objects.get(hash_id=p_v.pre_version)
                p_p_v_info = p_p_v.to_json()
                running_start_hash = p_p_v_info['running_start']
                running_end_hash = p_p_v_info['running_end']
                e_start = EventsHub.objects.get(hash_id=running_start_hash)
                e_end = EventsHub.objects.get(hash_id=running_end_hash)

                start_time = e_start.occur_datetime.strftime('%Y-%m-%d %H:%M:%S')
                end_time = e_end.occur_datetime.strftime('%Y-%m-%d %H:%M:%S')

                return "start_time:{start_time}, end_time:{end_time} <br><br> \n".format(start_time=start_time, end_time=end_time)
            except Exception as e:
                return 'success'

    def _re_run_program(self, p_v_info):
        pre_tables = p_v_info['pre_tables']
        for tid in pre_tables:
            if not pre_tables[tid]:
                table_obj = TablesInfo.objects.get(pk=tid)
                if table_obj.db_name in ('py_etl', 'py_fund_2_1', 'py_bond_2_1', 'py_stock_2_1', 'py_daziguan_2_1'):
                    if tid not in self.table_list:
                        self.table_list.append(tid)

    def _table_success(self):
        for tid in self.table_list:
            occur_datetime = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            table_info = TablesInfo.objects.get(pk=tid)
            db_server = table_info.db_server
            db_name = table_info.db_name
            table_name = table_info.table_name

            data = {'db_server': db_server, 'table_name': table_name,
                    'db_name': db_name, 'occur_datetime': occur_datetime}
            data = json.dumps(data)
            if db_server != 'db_153':
                try:
                    MysqlSyncLog(data)
                    print("success! {data}".format(data=data))
                except Exception as e:
                    print("failed! {data} {err}".format(data=data, err=e))


if __name__ == '__main__':
    g = GetCalInfo(1)
    result_string = g()
    print(result_string)
