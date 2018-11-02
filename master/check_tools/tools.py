import os
import django

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "master.settings")
django.setup()
from master_server.models import TablesInfo, PyScriptBaseInfoV2, ServerInfo, Path
import master_server.models as m
from urllib import request, parse
from django.db import connection

from master_server.mongo_models import EventsHub, TableVersionTree, TableInfo, CalProgramInfo, CalVersionTree

from master_server.packages.hash import get_hash
from master_server.collect_info_to_mq import SendProgramStatus
from master_server.packages.log_module import mysql_sync_result_reader as mr
from datetime import datetime
import time
from master_server import mongo_models as mo
import json
from master_server.packages.event_product import EventProduct
from time import sleep
from master_server.packages.mysql_sync_result import MysqlSyncLog


class MysqlSync:
    def __init__(self, db_name, table_name, hash_id=None):
        page = ''
        table = "{db_name}.{table_name}".format(db_name=db_name, table_name=table_name)
        if hash_id:
            sync_pai = {"table_name": table, "token": "MpaCG=xN8Q5XL0b>#SdEhcpD", "taskid": hash_id}
        else:
            sync_pai = {"table_name": table, "token": "MpaCG=xN8Q5XL0b>#SdEhcpD"}
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
            print(
                '{db_name}.{table_name}:{page}'.format(db_name=db_name, table_name=table_name, page=page))


def find_program_from_res(table_list, table_name=False):
    """
    根据结果表
    查询程序
    """
    if table_name:
        a = list()
        for t in table_list:
            table = TablesInfo.objects.filter(table_name=t).filter(db_server='db_153')
            print(table)
            if table:
                table_id = table[0].pk
                a.append(table_id)
        table_list = a
        print(table_list)
    for i in table_list:
        try:
            t = TablesInfo.objects.get(pk=int(i))
            db_name = t.db_name
            table_name = t.table_name
            t_153 = TablesInfo.objects.get(db_name=db_name, table_name=table_name, db_server='db_153')
        except Exception as e:
            print(e)
            t_153 = t
        print(str(i) + " " + t_153.db_server + "." + t_153.db_name + "." + t_153.table_name + ":")
        ss = PyScriptBaseInfoV2.objects.filter(result_tables=t_153)
        for s in ss:
            print("{0} {1} {2} {3}".format(s.sid, s.name, s.cron, s.owner))


def slave_exec_api(sid, version, subversion=False):
    """
    查询API所在的服务器，并返回url
    :return:
    """
    # connection_usable()
    # if not isinstance(subversion, int):
    #     subversion = int(time.time()) * 1000
    p = PyScriptBaseInfoV2.objects.get(sid=sid)
    api = '{0}{1}'.format(p.path.path, p.name)
    subversion = int(time.time()) * 1000
    parameter_str_1 = "?sid={sid}&version={version}&subversion={subversion}".format(sid=sid,
                                                                                    version=version,
                                                                                    subversion=subversion)

    parameter_str_2 = "?sid={sid}&version={version}".format(sid=sid, version=version,)

    if subversion:
        parameter_str = parameter_str_1
    else:
        parameter_str = parameter_str_2

    api = api + parameter_str

    print(api)
    data = {
        'url': api,
    }
    print(api)
    try:
        server = ServerInfo.objects.get(path__program__sid=sid)
        ip = server.ip
        port = server.port
        url = "http://{ip}:{port}/slave_server/exec_api/".format(ip=ip, port=port)
        print(url)
    except Exception as e:
        url = 'Can not find server ip port!'
        return url
    try:
        data = parse.urlencode(data).encode('utf-8')
        req = request.Request(url, data=data)
        page = request.urlopen(req).read()
        page = page.decode('utf-8')
        return page
    except Exception as e:
        return e


def exec_sql():
    sql = '''
insert into py_crontab.py_script_tables_info
select 0,
a.db_server,a.db_name,
a.TABLE_NAME,0
from
(select 'db_153' as db_server,TABLE_SCHEMA as db_name,TABLE_NAME from information_schema.`TABLES` where TABLE_SCHEMA like '%py_etl') a
LEFT JOIN py_crontab.py_script_tables_info b
on a.db_name = b.db_name
and a.db_server = b.db_server
and a.TABLE_NAME = b.TABLE_NAME
where b.TABLE_NAME is null
    '''
    with connection.cursor() as cursor:
        cursor.execute(sql)


def mysql_table(db_name):
    import pandas as pd
    import pymysql
    from sqlalchemy import create_engine
    mysql_cn1 = pymysql.connect(host='192.168.0.153', port=3306, user='pycf', passwd='1qaz@WSXabc')
    mysql_cn2 = pymysql.connect(host='192.168.0.153', port=3306, user='pycf', passwd='1qaz@WSXabc')
    engine = create_engine("mysql+pymysql://pycf:1qaz@WSXabc@192.168.0.153:3306/py_crontab?charset=utf8")
    # 这里一定要写成mysql+pymysql，不要写成mysql+mysqldb

    sql1 = '''SELECT
    0 as id , "{db_name}" AS db_server, table_schema as db_name, table_name, 
    0 AS data_source
FROM
information_schema.TABLES
WHERE
table_schema LIKE "%2_1%" or table_schema like "%_qc"'''.format(db_name=db_name)

    sql2 = '''insert into py_crontab.py_script_tables_info
select 0,
a.db_server,a.db_name,
a.TABLE_NAME,0
from
(select * from py_crontab.py_script_tables_info_tmp) a
LEFT JOIN py_crontab.py_script_tables_info b
on a.db_name = b.db_name
and a.db_server = b.db_server
and a.TABLE_NAME = b.TABLE_NAME
where b.TABLE_NAME is null
    '''

    cursor = mysql_cn2.cursor()
    cursor.execute('truncate py_crontab.py_script_tables_info_tmp')
    mysql_cn2.close()

    df1 = pd.read_sql(sql1, con=mysql_cn1)
    df1.to_sql(name='py_script_tables_info_tmp', con=engine, if_exists='append', index=False, index_label=False)

    mysql_cn2 = pymysql.connect(host='192.168.0.153', port=3306, user='pycf', passwd='1qaz@WSXabc')
    cursor = mysql_cn2.cursor()
    num = cursor.execute(sql2)
    mysql_cn2.commit()
    print(num)
    mysql_cn1.close()
    mysql_cn2.close()


def get_version(table, db):
    table_info = TablesInfo.objects.get(table_name=table, db_name=db, db_server='db_153')
    tid = table_info.pk
    table_info = TableInfo.objects.get(tid=tid)
    pointer = table_info.pointer
    t = TableVersionTree.objects.get(hash_id=pointer)
    pre_version = t.pre_version
    t = TableVersionTree.objects.get(hash_id=pre_version)
    program_list = t.program_version
    version = ''
    for p in program_list:
        try:
            event_hash = program_list[p]
            print(event_hash)
            event = EventsHub.objects.get(hash_id=event_hash)
            print(event.to_json())
            pre_version = event.version
            if not version:
                version = pre_version
            elif pre_version > version:
                version = pre_version
        except Exception as e:
            pass
    return version


class AliTest:
    def ali_table(self, table, db, occur_datetime):
        table_info = {'table_name': table, 'db_name': db, 'db_server': 'db_ali'}
        table = TablesInfo.objects.filter(**table_info)
        if not table:
            t = TablesInfo(**table_info)
            t.save()
            tid = t.pk
        else:
            tid = table[0].pk
        mr.info(tid)

        version = self._get_version(table, db)
        event_info = {'tid': tid, 'type': 101,
                      'info': 'table QC_success',
                      'occur_datetime': occur_datetime,
                      'version': version,
                      'source': "153-ali_sync"}
        hash_id = get_hash(event_info)
        event_info['hash_id'] = hash_id
        event = EventsHub(**event_info)
        event.save()
        SendProgramStatus(message=event_info, msg_type='t').send_msg()

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

    def _155_table(self, table, db, occur_datetime):
        table_info = {'table_name': table, 'db_name': db, 'db_server': 'db_155'}
        table = TablesInfo.objects.filter(**table_info)
        if not table:
            t = TablesInfo(**table_info)
            t.save()
            tid = t.pk
        else:
            tid = table[0].pk
        mr.info(tid)

        version = self._get_version(table, db)

        event_info = {'tid': tid, 'type': 101,
                      'info': 'table QC_success',
                      'occur_datetime': occur_datetime,
                      'version': version,
                      'source': "153-ali_sync"}
        hash_id = get_hash(event_info)
        event_info['hash_id'] = hash_id
        event = EventsHub(**event_info)
        event.save()
        SendProgramStatus(message=event_info, msg_type='t').send_msg()


class GetParentSon:
    def __init__(self, sid):
        self.entry = sid

        self.father_list = dict()
        self.son_list = dict()
        self._create_father_list(self.entry)
        self._create_son_list(self.entry)
        self._print_info()

    def _create_father_list(self, son_sid):
        tables = TablesInfo.objects.filter(son_program__pk=son_sid)
        programs_obj = set()
        for t in tables:
            # print(t.pk)
            try:
                t_name = t.table_name
                db_name = t.db_name
                table_153_obj = TablesInfo.objects.filter(table_name=t_name).filter(db_name=db_name).filter(db_server='db_153')[0]
                t = table_153_obj
            except Exception as e:
                pass
            p_o = PyScriptBaseInfoV2.objects.filter(result_tables=t)
            for p in p_o:
                programs_obj.add(p)

        for program in programs_obj:
            sid = program.pk
            name = program.name
            cron = program.cron
            owner = program.owner
            func = program.function

            if str(sid) in self.father_list:
                if son_sid not in self.father_list[str(sid)]['son']:
                    self.father_list[str(sid)]['son'].append(son_sid)
            else:
                self.father_list[str(sid)] = {'info': (name, cron, owner, func), 'son': [son_sid, ]}
        if programs_obj:
            for program in programs_obj:
                if program.pk != son_sid:
                    self._create_father_list(program.pk)

    def _create_son_list(self, father_sid):
        tables = TablesInfo.objects.filter(father_program__pk=father_sid)
        programs_obj = set()
        for t in tables:
            try:
                t_name = t.table_name
                db_name = t.db_name
                table_153_obj = TablesInfo.objects.filter(table_name=t_name).filter(db_name=db_name).filter(db_server='db_153')[0]
                t = table_153_obj
            except Exception as e:
                pass
            p_o = PyScriptBaseInfoV2.objects.filter(pre_tables=t)
            for p in p_o:
                programs_obj.add(p)

        for program in programs_obj:
            sid = program.pk
            name = program.name
            cron = program.cron
            owner = program.owner.pk
            func = program.function

            if str(sid) in self.son_list:
                if father_sid not in self.son_list[str(sid)]['father']:
                    self.son_list[str(sid)]['father'].append(father_sid)
            else:
                self.son_list[str(sid)] = {'info': (name, cron, owner, func), 'father': [father_sid, ]}
        if programs_obj:
            for program in programs_obj:
                if program.pk != father_sid:
                    self._create_son_list(program.pk)

    def _print_info(self):
        s_obj = PyScriptBaseInfoV2.objects.get(pk=self.entry)
        s_obj_name = s_obj.name
        cron = s_obj.cron
        owner = s_obj.owner
        func = s_obj.function
        print('{0} {1} {2} {3}'.format(s_obj_name, cron, owner, func))
        print('father_list:')
        for i in self.father_list:
            print('{0}, {1}'.format(i, self.father_list[i]))
        print('son_list:')
        for i in self.son_list:
            print('{0}, {1}'.format(i, self.son_list[i]))


def table_success(tid, version=None):
    if not version:
        version = datetime.now().strftime('%Y-%m-%d')
    occur_datetime = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    event_info = {'tid': tid, 'type': 101,
                  'info': 'table QC_success',
                  'occur_datetime': occur_datetime,
                  'version': version,
                  'source': "data cha bu"}
    hash_id = get_hash(event_info)
    event_info['hash_id'] = hash_id

    SendProgramStatus(message=event_info, msg_type='t').send_msg()


def get_cal_tree(sid, pre=0):
    c_i = mo.CalProgramInfo.objects.get(sid=sid)
    pointer = c_i.pointer
    c_t = mo.CalVersionTree.objects.get(hash_id=pointer)
    print(c_t.to_json())
    for i in range(pre):
        hash_id = c_t.hash_id
        c_t = get_cal_pre_tree(hash_id)
        if not c_t:
            return
        print(c_t.to_json())


def get_cal_pre_tree(hash_id):
    c_t = mo.CalVersionTree.objects.get(hash_id=hash_id)
    hash_id = c_t.pre_version
    if hash_id == 'init':
        return False
    c_t = mo.CalVersionTree.objects.get(hash_id=hash_id)
    return c_t


def get_cron_tree(sid, pre=0):
    c_i = mo.CronProgramInfo.objects.get(sid=sid)
    pointer = c_i.pointer
    c_t = mo.CronProgramVersionTree.objects.get(hash_id=pointer)
    print(c_t.to_json())
    for i in range(pre):
        hash_id = c_t.hash_id
        c_t = get_cron_pre_tree(hash_id)
        if not c_t:
            return
        print(c_t.to_json())


def get_cron_pre_tree(hash_id):
    c_t = mo.CronProgramVersionTree.objects.get(hash_id=hash_id)
    hash_id = c_t.pre_version
    if hash_id == 'init':
        return False
    c_t = mo.CronProgramVersionTree.objects.get(hash_id=hash_id)
    return c_t


def get_program_from_path():
    program_list = [program.pk for program in PyScriptBaseInfoV2.objects.filter(path__pk=51)]
    return program_list


def flush_program(start_hour, end_hour, version=None):
    programs = PyScriptBaseInfoV2.objects.filter(program_type=0)
    for p in programs:
        cron = p.cron
        try:
            hour = int(cron.split()[1])
        except Exception as e:
            print("err" + str(p.pk) + cron)
            continue
        day = cron.split()[4]
        if day == '*' and start_hour <= hour <= end_hour:
            print(p.pk)
            status = False
            while True:
                try:
                    send_program_ok(p.pk, version)
                    # a = slave_exec_api(p.pk, version, True)
                    # print(a)
                    status = True
                except Exception as e:
                    status = False
                finally:
                    if status:
                        break
            sleep(60)


def send_program_ok(sid, version=None):
    if not version:
        version = str(datetime.today().date())
    version = '{version} 00:00:00'.format(version=version)
    subversion = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    occur_datetime = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

    source = "手动插补"
    event_info = {'sid': sid, 'type': 1, 'info': '', 'version': version,
                  'subversion': subversion, 'occur_datetime': occur_datetime, 'source': source}

    hash_id = get_hash(event_info)
    event_info['hash_id'] = hash_id
    event = EventsHub(**event_info)
    event.save()

    event_info_message = {'sid': sid, 'hash_id': hash_id, 'subversion': subversion,
                          'version': version, 'type': 1, 'occur_datetime': occur_datetime}
    message = json.dumps(event_info_message)
    event_product = EventProduct()
    event_product.broadcast_message(message=message)

    sleep(2)

    event_info = {'sid': sid, 'type': 2, 'info': '', 'version': version,
                  'subversion': subversion, 'occur_datetime': occur_datetime, 'source': source}

    hash_id = get_hash(event_info)
    event_info['hash_id'] = hash_id
    event = EventsHub(**event_info)
    event.save()

    event_info_message = {'sid': sid, 'hash_id': hash_id, 'subversion': subversion,
                          'version': version, 'type': 2, 'occur_datetime': occur_datetime}
    message = json.dumps(event_info_message)
    event_product = EventProduct()
    event_product.broadcast_message(message=message)


def get_sync_miss_table():
    table_list = list()
    i = 0
    for p in CalProgramInfo.objects.all():
        p_v = CalVersionTree.objects.get(hash_id=p.pointer)
        if p_v.pre_version == 'init':
            i = i + 1
            p_v_info = json.loads(p_v.to_json())
            print('{num}======='.format(num=i))
            print(p_v_info)
            pre_tables = p_v_info['pre_tables']
            for tid in pre_tables:
                if not pre_tables[tid]:
                    table_obj = TablesInfo.objects.get(pk=tid)
                    if table_obj.db_name in ('py_etl', 'py_fund_2_1', 'py_bond_2_1', 'py_stock_2_1', 'py_daziguan_2_1'):
                        table_name = '{db}.{table}'.format(db=table_obj.db_name, table=table_obj.table_name)
                        if table_name not in table_list:
                            table_list.append(table_name)
    print(table_list)
    for i in table_list:
        db_name, table_name = i.split(".")
        print(db_name, table_name)
        tables = TablesInfo.objects.filter(table_name=table_name, db_name=db_name)
        occur_datetime = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        for table_info in tables:
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


if __name__ == "__main__":
    date_today = datetime.now()
    date_today = date_today.strftime('%Y-%m-%d')
    # get_sync_miss_table()
    """
    刷新依赖关系
    """
    # mysql_table('db_153')
    # flush_program(15, 15, date_today)
    # flush_program(0, 9, date_today)
    # send_program_ok(651, '2018-08-16')

    """
    获取树结构
    """
    # get_cron_tree(757, 3)
    # get_cal_tree(757, 10)
    # get_cal_tree(671, 10)


    """
    获取依赖关系
    """
    # a = GetParentSon(466)
    # a = GetParentSon(651)

    """
    表结果更新
    """
    # tid = [3324]
    # for t in tid:
    #     table_success(t)

    """
    重新调用程序
    """

    for i in [503]:
        a = slave_exec_api(i, date_today)
        print(a)


    # a = slave_exec_api(324, 'http://192.168.0.157:3555/macro_v2/bondManagerController/usdCnyIndexDay?version=2018-05-25&sid=324')
    # print(a)
    # exec_sql()

    """
    根据结果找程序
    """
    # find_program_from_res([11577,])
    # a = ['py_bond_2_1.py_bond_product_abs_base_info_2_1',
    #      'py_etl.py_etl_bond_financial_issuer_financial_indicators_2_1',
    #      'py_etl.py_etl_bond_non_financial_issuer_financial_indicators_2_1', ]

    # find_program_from_res([4685, 5087])
    # find_program_from_res([2396, 2534])
    # find_program_from_res([2515,2520])
    # find_program_from_res([2475, 2832, 2947])

    # p_list = PyScriptBaseInfoV2.objects.filter(path__pk=51)
    # for i in p_list:
    #     print(i.pk)
    #     a = slave_exec_api(i.pk, '2018-06-08')
    #     print(a)
    #     sleep(20)
    # path = Path.objects.filter()
    # for p in path:
    #     print(p.pk)
    #     print(p)

    # mysql_table('db_153')
    #for i in range(519, 536):
    #    a = slave_exec_api(i, '2018-06-27')
    #    print(a)

    """
    表同步
    """
    # get_sync_miss_table()

    # a = ['py_daziguan_2_1.py_hgyz_interbank_lending_day']
    # for i in a:
    #     db_name, table_name = i.split(".")
    #     print(db_name, table_name)
    #     sleep(3)
    #     mq = MysqlSync(db_name, table_name)

    # 同步库中所有表
    # a = TablesInfo.objects.filter(db_server='db_153')
    # for i in a:
    #     if i.db_name in ('py_etl', 'py_bond_2_1', 'py_fund_2_1', 'py_daziguan_2_1', 'py_stock_2_1'):
    #         table = "{db_name}.{table_name}".format(db_name=i.db_name, table_name=i.table_name)
    #         db_name, table_name = table.split(".")
    #         print(db_name, table_name)
    #         sleep(1)
    #         mq = MysqlSync(db_name, table_name)

    """ 
    查询程序的结果表
    """
    # table = TablesInfo.objects.filter(son_program__sid=578)
    # for t in table:
    #    print(t)
    # t = m.TablesInfo.objects.filter(father_program__sid=510)
    # print(t)
    #
    # i = 0
    # for p in mo.CalProgramInfo.objects.all():
    #     p_v = mo.CalVersionTree.objects.get(hash_id=p.pointer)
    #     p_v = mo.CalVersionTree.objects.get(hash_id=p_v.pre_version)
    #     if p_v.status == 4:
    #         i = i + 1
    #         print('{num}======='.format(num=i))
    #         a = slave_exec_api(p_v.sid, '2018-08-08')
    #         print(a)

    # table_list = list()
    # i = 0
    # for p in CalProgramInfo.objects.all():
    #     p_v = CalVersionTree.objects.get(hash_id=p.pointer)
    #     if p_v.pre_version == 'init':
    #         i = i + 1
    #         p_v_info = json.loads(p_v.to_json())
    #         # print('{num}======='.format(num=i))
    #         # print(p_v_info)
    #         pre_tables = p_v_info['pre_tables']
    #         num = 0
    #         for tid in pre_tables:
    #             if pre_tables[tid] == '':
    #                 num=1
    #                 break
    #         if num == 0:
    #             print(p_v.sid)
    #             print(p_v_info)
    #             a = slave_exec_api(p_v.sid, date_today)
    #             print(a)



