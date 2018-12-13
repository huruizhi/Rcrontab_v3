from master_server.mongo_models import CalVersionTree, EventsHub, TableInfo, TableVersionTree
from master_server.packages.hash import get_hash
from master_server.schedulers.schedulers import Scheduler
from master_server.packages.log_module import cal_log
import json
from datetime import timedelta, datetime
from master_server.models import PyScriptBaseInfoV2, TablesInfo


class CalTreeObj:
    def __init__(self, sid, pre_tables, hash_id=None, pre_version=None, init=False):
        self.sid = sid
        self.info_dict = dict()
        if not hash_id:
            self.create_new_obj(sid, pre_tables=pre_tables, pre_version=pre_version, init=init)
        else:
            self.get_old_obj(hash_id)

    # 获取存在的对象
    def get_old_obj(self, hash_id):
        info = dict()
        try:
            info_obj = CalVersionTree.objects.get(hash_id=hash_id)
            # 转换成字典
            info = dict(info_obj.to_mongo())
            # 去掉Objectid
            info.pop('_id')
        finally:
            self.info_dict = info

    # 创建新的对象
    def create_new_obj(self, sid, pre_tables, pre_version=None, init=False):
        pre_tables_dict = dict()
        for table in pre_tables:
            pre_tables_dict[str(table)] = ''
            try:
                table_obj = TablesInfo.objects.get(pk=int(table))
                t_name = table_obj.table_name
                db_name = table_obj.db_name
                table_153_obj = TablesInfo.objects.filter(table_name=t_name).filter(db_name=db_name).filter(db_server='db_153')[0]
                table_153 = table_153_obj.pk
            except Exception as e:
                table_153 = table
            programs = PyScriptBaseInfoV2.objects.filter(result_tables__pk=int(table_153))
            if len(programs) == 0:
                pre_tables_dict[str(table)] = 'manual'
            elif not self._daily_update(table_153):
                pre_tables_dict[str(table)] = 'not_daily_update'
            elif self._depend_on_self(table):
                pre_tables_dict[str(table)] = 'depend_on_self'
            elif init:
                hash_id = self._is_update_today(table)
                pre_tables_dict[str(table)] = hash_id

        if not pre_version:
            pre_version = 'init'
        info = {'sid': sid, 'status': 0, 'pre_version': pre_version, 'pre_tables': pre_tables_dict}
        hash_id = get_hash(json.dumps(info))
        info['hash_id'] = hash_id
        version_tree = CalVersionTree(**info)
        version_tree.save()
        self.info_dict = info
        cal_log.info("in tree:" + self.info_dict['hash_id'])

    @staticmethod
    def _daily_update(tid):
        programs = PyScriptBaseInfoV2.objects.filter(result_tables__pk=int(tid))
        for p in programs:
            cron = p.cron
            if not cron:
                pass
            else:
                cron = cron.split()
                for c in cron[2:]:
                    if c != '*':
                        return False
        return True

    @staticmethod
    def _is_update_today(tid):
        status = ''
        t_id = tid
        try:
            table = TablesInfo.objects.get(pk=tid)
            table_name = table.table_name
            db_name = table.db_name
            table = TablesInfo.objects.filter(table_name=table_name, db_name=db_name, db_server='db_153')
            if table:
                t_id = table[0].pk
        except Exception as e:
            t_id = tid

        program = PyScriptBaseInfoV2.objects.filter(result_tables__pk=t_id)
        for p in program:
            p_type = p.program_type
            if p_type != 0:
                return status

        now = datetime.now()
        datetime_line = '{date} 10:00:00'.format(date=now.strftime('%Y-%m-%d'))
        datetime_line = datetime.strptime(datetime_line, '%Y-%m-%d %H:%M:%S')
        if datetime_line > now:
            return status

        try:
            table = TableInfo.objects.get(tid=int(t_id))
            next_hash = table.pointer
            table_version = TableVersionTree.objects.get(hash_id=next_hash)
            if table_version.QC_status == 100:
                pre_version = table_version.pre_version
                table_pre_version = TableVersionTree.objects.get(hash_id=pre_version)
                event = EventsHub.objects.get(hash_id=table_pre_version.QC_success)
                occur_datetime = event.occur_datetime
                if now >= occur_datetime >= datetime_line:
                    source = event.source
                    status = source.split(':')[1]
        finally:
            return status

    def _depend_on_self(self, tid):
        programs = PyScriptBaseInfoV2.objects.filter(result_tables__pk=tid)
        for p in programs:
            if p.sid == self.sid:
                return True
        return False

    # 程序开始执行
    def running_start(self, event_hash_id):
        # 更新info信息
        self.info_dict['status'] = 1
        self.info_dict['running_start'] = event_hash_id
        self._update_info()
        self.del_start_scheduler()

    # 程序执行成功
    def running_end_success(self, event_hash_id):
        # 更新info信息
        self.info_dict['status'] = 2
        self.info_dict['running_end'] = event_hash_id
        self._update_info()
        self.del_end_scheduler()

    # 程序执行失败
    def running_end_failed(self, event_hash_id):
        # 更新info信息
        self.info_dict['status'] = 3
        self.info_dict['running_end'] = event_hash_id
        self._update_info()
        self.del_end_scheduler()

    # 程序开始miss
    def running_miss_start(self, event_hash_id):
        self.info_dict['status'] = 4
        self.info_dict['running_start'] = event_hash_id
        self._update_info()
        self.del_end_scheduler()

    # 没有返回执行结果
    def running_end_miss(self, event_hash_id):
        # 更新info信息
        self.info_dict['status'] = 5
        self.info_dict['running_end'] = event_hash_id
        self._update_info()

    # 更新tree信息
    def _update_info(self):
        cal_log.info("update tree {sid}".format(sid=self.sid))
        tree_obj = CalVersionTree.objects(hash_id=self.info_dict['hash_id'])
        tree_obj.update(**self.info_dict)

    # 设置deadline
    def set_deadline_scheduler(self):
        version = datetime.now()
        begin_time_out = (version + timedelta(minutes=10)).strftime('%Y-%m-%d %H:%M:%S')
        cal_tree_hash_start = '{0}_start'.format(self.sid)
        Scheduler.add_job_deadline(cron_tree_hash=cal_tree_hash_start, date_time=begin_time_out, status='start',
                                   sid=self.sid)

        cal_tree_hash_end = '{0}_end'.format(self.sid)
        end_time_out = (version + timedelta(hours=3)).strftime('%Y-%m-%d %H:%M:%S')
        Scheduler.add_job_deadline(cron_tree_hash=cal_tree_hash_end, date_time=end_time_out, status='end',
                                   sid=self.sid)

    # 删除开始定时器
    def del_start_scheduler(self):
        hash_id = '{0}_start'.format(self.sid)
        Scheduler.remove_job(job_id=hash_id)

    # 删除结束定时器
    def del_end_scheduler(self):
        hash_id = '{0}_end'.format(self.sid)
        Scheduler.remove_job(job_id=hash_id)

    # 前置表更新成功
    def pre_table_done(self, tid, hash_id):
        tid = str(tid)
        depend_on_self = False
        if tid in self.info_dict['pre_tables']:
            if self.info_dict['pre_tables'][tid] == 'depend_on_self':
                depend_on_self = True
            self.info_dict['pre_tables'][tid] = hash_id
        else:
            self.info_dict['pre_tables'][tid] = hash_id
            raise Exception("{tid} not in {sid} pre_tables".format(tid=tid, sid=self.sid))
        self._update_info()
        return depend_on_self

    # 检查前置表 是否都 准备OK
    def check_pre_tables(self):
        is_ok = 1
        for table in self.info_dict['pre_tables']:
            if self.info_dict['pre_tables'][table] == '':
                is_ok = 0
                return is_ok
        return is_ok

    # 修改前置表
    def change_pre_tables(self, pre_tables):
        if set(pre_tables) != set(self.info_dict['pre_tables']):
            pre_tables_dict = dict()
            for table in pre_tables:
                pre_tables_dict = {str(table): ''}
            self.info_dict['pre_tables'] = pre_tables_dict
            self._update_info()

    # 判断程序是否在正在执行
    def is_running(self):
        if self.info_dict['status'] == 1:
            return True
        else:
            return False
