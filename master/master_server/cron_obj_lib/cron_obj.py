from master_server.packages.hash import get_hash_ack
from master_server.cron_obj_lib.cron_Info_obj import CronInfoObj
from master_server.cron_obj_lib.cron_tree_obj import CronTreeObj
from master_server.packages.receive import ReceiveRabbitMQMessage
from master_server.packages.log_module import WriteLog
from master_server.models import TablesInfo
import json
from threading import Thread
from time import sleep
from master_server.mysqlsyncAPI.mysql_sync import mysql_sync_func


class CronObj:

    def __init__(self, sid, pre_tables, result_tables, cron, api, server_id):
        self.sid = sid
        self.server_id = server_id

        info_dict_new = {'sid': sid, 'result_tables': result_tables, 'pre_tables': pre_tables,
                         'cron': cron, 'api': api}

        # 记录信息的hash值用于之后的比较
        self.hash_ack = get_hash_ack(info_dict_new)

        # 创建CronInfoObj对象
        self.cron_info_obj = CronInfoObj(sid, pre_tables, result_tables, cron, api, server_id, self.hash_ack)

        # 创建CronTreeObj对象

        if self.cron_info_obj.pointer:
            try:
                self.cron_tree_obj = CronTreeObj(sid=self.sid, hash_id=self.cron_info_obj.pointer)
            except Exception as e:
                self.cron_tree_obj = CronTreeObj(sid=self.sid)
        else:
            self.cron_tree_obj = CronTreeObj(sid=self.sid)

        # 获取指针 更新到CronInfoObj对象
        self.cron_info_obj.change_pointer(pointer=self.cron_tree_obj.info_dict['hash_id'])

        # 开启监听器
        thread = Thread(target=self.events_listener)
        thread.start()

    # 刷新CronObj 基础信息
    def refresh(self, sid, pre_tables, result_tables, cron, api, server_id):
        if sid == self.sid:
            info_dict_new = {'sid': sid, 'result_tables': result_tables, 'pre_tables': pre_tables,
                             'cron': cron, 'api': api}
            hash_ack_new = get_hash_ack(info_dict_new)

            # 程序信息更新
            if hash_ack_new != self.hash_ack:
                self.hash_ack = hash_ack_new
                self.cron_info_obj.info_change(sid, pre_tables, result_tables, cron, api, hash_ack_new)
                self.cron_tree_obj.update_dead_line()

            # 程序部署服务器更改
            if self.server_id != server_id:
                self.server_id = server_id
                self.cron_info_obj.server_change(self.server_id)

    # 事件监听器
    def events_listener(self):
        while True:
            try:
                mq = ReceiveRabbitMQMessage(name=str(self.sid), target=self.callback)
                mq.start()
            except Exception as e:
                sleep(1)

    # 事件回调函数
    def callback(self, ch, method, properties, body):
        logging = WriteLog(name="events_listener")
        try:
            log_str = body.decode('utf-8')
            log_dict = json.loads(log_str)

            # 确定事件为该队列信息
            if 'sid' in log_dict and log_dict['sid'] == self.sid:
                logging.info(log_str)
            else:
                return

            cron_tree_status = self.cron_tree_obj.info_dict['status']

            # 获取事件信息
            hash_id = log_dict['hash_id']
            status = log_dict['type']

            if cron_tree_status == 0 and status == 1:
                subversion = log_dict['subversion']
                version = log_dict['version']
                self.running_start_event(hash_id, subversion, version)
            elif cron_tree_status == 1 and status in (2, 3):
                subversion = log_dict['subversion']
                self.running_end_event(status=status, hash_id=hash_id, subversion=subversion)
                self._broadcast_result()
            elif cron_tree_status == 0 and status == 4:
                self.unusual_end(status=status, hash_id=hash_id)
                self._broadcast_result()
            elif status == 5:
                subversion = log_dict['subversion']
                self.unusual_end(status=status, hash_id=hash_id, subversion=subversion)
                self._broadcast_result()
        except Exception as e:
            logging("{name}:{err}".format(name=__name__, err=str(e)))
        finally:
            ch.basic_ack(delivery_tag=method.delivery_tag)

    #  异常退出
    def unusual_end(self, status, hash_id, subversion=None):
        # 执行结果正确
        if status == 4:
            self.miss_start(hash_id)
        # 执行结果错误
        if status == 5:
            if self.cron_tree_obj.info_dict['subversion'] == subversion:
                self.miss_end(hash_id)

    # 更新tree对象 为 running start
    def running_start_event(self, hash_id, subversion, version=None):
        self.cron_tree_obj.running_start(event_hash_id=hash_id, subversion=subversion, version=version)

    # 更新tree对象 状态
    def running_end_event(self, status, hash_id, subversion):
        if self.cron_tree_obj.info_dict['subversion'] != subversion:
            pass
        # 执行结果正确
        if status == 2:
            self.running_success(hash_id)
        # 执行结果错误
        if status == 3:
            self.running_failed(hash_id)

    # 程序执行成功
    def running_success(self, hash_id):
        # 修改当前 tree 对象信息
        self.cron_tree_obj.running_end_success(event_hash_id=hash_id)
        # 创建新的 tree对象
        self._create_new_tree_obj()

    # 程序执行失败
    def running_failed(self, hash_id):
        # 修改当前 tree 对象信息
        self.cron_tree_obj.running_end_failed(event_hash_id=hash_id)
        # 创建新的 tree对象
        self._create_new_tree_obj()

    # 创建新tree对象
    def _create_new_tree_obj(self):
        print(__name__ + ":")
        pre_version = self.cron_tree_obj.info_dict['hash_id']
        print(pre_version)
        del self.cron_tree_obj
        self.cron_tree_obj = CronTreeObj(sid=self.sid, pre_version=pre_version)
        self.cron_info_obj.change_pointer(pointer=self.cron_tree_obj.info_dict['hash_id'])

    # 开始miss
    def miss_start(self, hash_id):
        self.cron_tree_obj.running_miss_start(event_hash_id=hash_id)
        self._create_new_tree_obj()

    # 结果miss
    def miss_end(self, hash_id):
        self.cron_tree_obj.running_end_miss(event_hash_id=hash_id)
        self._create_new_tree_obj()

    def delete_obj(self):
        self.cron_info_obj.drop_exec_plan()
        self.cron_info_obj.del_scheduler()
        self.cron_tree_obj.del_dead_line_scheduler()
        del self.cron_info_obj
        del self.cron_tree_obj

    def _broadcast_result(self):
        result_tables = TablesInfo.objects.filter(father_program__sid=self.sid)
        for tid in result_tables:
            thread = Thread(target=mysql_sync_func, args=(tid.pk,))
            thread.start()



