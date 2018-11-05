from master_server.packages.receive import ReceiveRabbitMQMessage
from master_server.cal_obj_lib.cal_info_obj import CalInfoObj
from master_server.cal_obj_lib.cal_tree_obj import CalTreeObj
from master_server.packages.hash import get_hash_ack
from master_server.packages.log_module import cal_log
from master_server.packages.mysql_check import connection_usable
from threading import Thread
import json
import time
from datetime import datetime
from master_server.packages.slave_exec_api import slave_exec_api
from master_server.models import TablesInfo
from master_server.mysqlsyncAPI.mysql_sync import mysql_sync_func


class CalObj:
    def __init__(self, sid, pre_tables, result_tables, api):
        log = "create new obj {sid}".format(sid=sid)
        cal_log.info(__name__ + log)
        self.sid = int(sid)

        info_dict_new = {'sid': sid, 'result_tables': result_tables, 'pre_tables': pre_tables,
                         'api': api}

        print(info_dict_new)
        # 记录信息的hash值用于之后的比较
        self.hash_ack = get_hash_ack(info_dict_new)

        # 创建CalInfoObj对象
        self.cal_info_obj = CalInfoObj(sid, pre_tables, result_tables, api, self.hash_ack)

        # 创建CalTreeObj对象
        if self.cal_info_obj.pointer:
            try:
                self.cal_tree_obj = CalTreeObj(sid=self.sid, hash_id=self.cal_info_obj.pointer,
                                               pre_tables=pre_tables)
            except Exception as e:
                self.cal_tree_obj = CalTreeObj(sid=self.sid, pre_tables=pre_tables, init=True)
        else:
            self.cal_tree_obj = CalTreeObj(sid=self.sid, pre_tables=pre_tables, init=True)

        # 获取指针 更新到CalInfoObj对象
        print(self.cal_tree_obj.info_dict)
        self.cal_info_obj.change_pointer(pointer=self.cal_tree_obj.info_dict['hash_id'])

        # 开启监听器
        thread = Thread(target=self.table_events_listener)
        thread.start()
        thread = Thread(target=self.program_events_listener)
        thread.start()
        is_ok = self.cal_tree_obj.check_pre_tables()
        if is_ok:
            time_now = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            self.exec_api(time_now)

    # 刷新CronObj 基础信息
    def refresh(self, sid, pre_tables, result_tables, api):
        sid = int(sid)
        if sid == self.sid:
            info_dict_new = {'sid': sid, 'result_tables': result_tables, 'pre_tables': pre_tables,
                             'api': api}

            hash_ack_new = get_hash_ack(info_dict_new)
            # 程序信息更新
            if hash_ack_new != self.hash_ack:
                self.hash_ack = hash_ack_new
                self.cal_info_obj.info_change(sid, pre_tables, result_tables, api, self.hash_ack)
                self.cal_tree_obj.change_pre_tables(pre_tables=pre_tables)
                return True
            else:
                return False
        return False

    def table_events_listener(self):
        while True:
            try:
                mq = ReceiveRabbitMQMessage(name=str(self.sid), target=self.table_callback, exchange='table_events')
                mq.start()
            except Exception as e:
                time.sleep(30)

    def table_callback(self, ch, method, properties, body):
        try:
            connection_usable()
            log_str = body.decode('utf-8')
            log_dict = json.loads(log_str)
            if 'tid' in log_dict:
                tid = log_dict['tid']
                if tid in self.cal_info_obj.info_dict['pre_tables']:
                    cal_log.info("{sid}:{tid} {log_str}".format(sid=self.sid, tid=tid, log_str=log_str))
                else:
                    return
                hash_id = log_dict['hash_id']
                version = log_dict['version']
                depend_on_self = self.cal_tree_obj.pre_table_done(tid=tid, hash_id=hash_id)
                if not depend_on_self:
                    is_ok = self.cal_tree_obj.check_pre_tables()
                    cal_log.info("{sid}:{is_ok}".format(sid=self.sid, is_ok=is_ok))
                    is_running = self.cal_tree_obj.is_running()
                    if is_ok and not is_running:
                        self.exec_api(version)
        except Exception as e:
            cal_log.error("{name}:{sid}:{err}".format(name=__name__, sid=self.sid, err=str(e)))
        finally:
            ch.basic_ack(delivery_tag=method.delivery_tag)

    # 执行api调用
    def exec_api(self, version):
        subversion = int(time.time()) * 1000
        version = version.split()[0]
        api = self.cal_info_obj.info_dict['api']
        try:
            self.cal_tree_obj.set_deadline_scheduler()
            api, page = slave_exec_api(sid=self.sid, api=api, version=version, subversion=subversion)
            cal_log.info("url:{url}\nresult:{page}".format(url=api, page=page))
        except Exception as e:
            cal_log.error("url:{url}\nerror:{err}".format(url=api, err=e))

    # 事件监听器
    def program_events_listener(self):
        while True:
            try:
                name = "{sid}-t".format(sid=str(self.sid))
                mq = ReceiveRabbitMQMessage(name=name, target=self.program_callback)
                mq.start()
            except Exception as e:
                time.sleep(30)

    # 事件回调函数
    def program_callback(self, ch, method, properties, body):
        try:
            connection_usable()
            log_str = body.decode('utf-8')
            log_dict = json.loads(log_str)

            # 确定事件为该队列信息
            if 'sid' in log_dict and int(log_dict['sid']) == self.sid:
                cal_log.info(log_str)
            else:
                return

            cal_tree_status = self.cal_tree_obj.info_dict['status']

            # 获取事件信息
            hash_id = log_dict['hash_id']
            status = log_dict['type']

            if cal_tree_status == 0 and status == 1:
                self.running_start_event(hash_id)
            elif cal_tree_status == 1 and status in (2, 3):
                self.running_end_event(status=status, hash_id=hash_id)
                self._broadcast_result()
            elif cal_tree_status == 0 and status == 4:
                self._broadcast_result()
                self.unusual_end(status=status, hash_id=hash_id)
            elif cal_tree_status == 1 and status == 5:
                self.unusual_end(status=status, hash_id=hash_id)
                self._broadcast_result()
        except Exception as e:
            cal_log.error("{name}:{err}".format(name=__name__, err=str(e)))
        finally:
            time.sleep(1)
            ch.basic_ack(delivery_tag=method.delivery_tag)

    #  异常退出
    def unusual_end(self, status, hash_id):
        # 执行结果错误
        if status == 5:
            self.miss_end(hash_id)
        if status == 4:
            self.miss_start(hash_id)

    # 更新tree对象 为 running start
    def running_start_event(self, hash_id):
        self.cal_tree_obj.running_start(event_hash_id=hash_id)

    # 更新tree对象 状态
    def running_end_event(self, status, hash_id):
        # 执行结果正确
        if status == 2:
            self.running_success(hash_id)
        # 执行结果错误
        if status == 3:
            self.running_failed(hash_id)

    # 程序执行成功
    def running_success(self, hash_id):
        # 修改当前 tree 对象信息
        self.cal_tree_obj.running_end_success(event_hash_id=hash_id)
        # 创建新的 tree对象
        self._create_new_tree_obj()

    # 程序执行失败
    def running_failed(self, hash_id):
        # 修改当前 tree 对象信息
        self.cal_tree_obj.running_end_failed(event_hash_id=hash_id)
        # 创建新的 tree对象
        self._create_new_tree_obj()

    # 创建新tree对象
    def _create_new_tree_obj(self):
        pre_version = self.cal_tree_obj.info_dict['hash_id']
        tables_obj = TablesInfo.objects.filter(son_program__pk=int(self.sid))
        pre_tables = [t.pk for t in tables_obj]
        del self.cal_tree_obj
        self.cal_tree_obj = CalTreeObj(sid=self.sid, pre_tables=pre_tables, pre_version=pre_version)
        self.cal_info_obj.change_pointer(pointer=self.cal_tree_obj.info_dict['hash_id'])

    # 程序没有结束
    def miss_end(self, hash_id):
        self.cal_tree_obj.running_end_miss(event_hash_id=hash_id)
        self._create_new_tree_obj()

    # 开始miss
    def miss_start(self, hash_id):
        self.cal_tree_obj.running_miss_start(event_hash_id=hash_id)
        self._create_new_tree_obj()

    def _broadcast_result(self):
        result_tables = self.cal_info_obj.info_dict['result_tables']
        for tid in result_tables:
            mysql_sync_func(tid)


