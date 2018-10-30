from master_server.mongo_models import CronProgramVersionTree
from master_server.packages.hash import get_hash
from master_server.schedulers.schedulers import Scheduler
import json


class CronTreeObj:
    def __init__(self, sid, hash_id=None, pre_version=None):
        self.sid = sid
        self.info_dict = dict()
        if hash_id:
            self.get_old_obj(hash_id)
        else:
            self.create_new_obj(sid, pre_version)
        # self.del_dead_line_scheduler()

    # 获取存在的对象
    def get_old_obj(self, hash_id):
        info = dict()
        try:
            info_obj = CronProgramVersionTree.objects.get(hash_id=hash_id)
            # 转换成字典
            info = dict(info_obj.to_mongo())
            # 去掉Objectid
            info.pop('_id')
        except Exception as e:
            print(e)
        finally:
            self.info_dict = info

    # 创建新的对象
    def create_new_obj(self, sid, pre_version=None):
        if not pre_version:
            pre_version = 'init'
        info = {'sid': sid, 'status': 0, 'pre_version': pre_version}
        next_run_time = Scheduler.get_job_next_run_time(job_id=str(sid)).strftime("%Y-%m-%d %H:%M:%S")
        info['next_run_time'] = next_run_time
        hash_id = get_hash(json.dumps(info))
        info['hash_id'] = hash_id
        version_tree = CronProgramVersionTree(**info)
        version_tree.save()
        self.info_dict = info
        print("in tree:" + self.info_dict['hash_id'])

    # 程序开始执行
    def running_start(self, event_hash_id, subversion, version=''):

        # 更新info信息
        self.info_dict['status'] = 1
        self.info_dict['running_start'] = event_hash_id
        self.info_dict['subversion'] = subversion
        self.info_dict['version'] = version
        self._update_info()

        # 设置删除开始dead_line
        self.del_start_scheduler()

    # 程序开始miss
    def running_miss_start(self, event_hash_id):
        self.info_dict['status'] = 4
        self.info_dict['running_start'] = event_hash_id
        self._update_info()

        # 删除结束定时器
        self.del_end_scheduler()

    # 程序执行成功
    def running_end_success(self, event_hash_id):
        # 删除定时器
        self.del_end_scheduler()

        # 更新info信息
        self.info_dict['status'] = 2
        self.info_dict['running_end'] = event_hash_id
        self._update_info()

    # 程序执行失败
    def running_end_failed(self, event_hash_id):
        # 删除定时器
        self.del_end_scheduler()

        # 更新info信息
        self.info_dict['status'] = 3
        self.info_dict['running_end'] = event_hash_id
        self._update_info()

    # 没有返回执行结果
    def running_end_miss(self, event_hash_id):
        # 更新info信息
        self.info_dict['status'] = 5
        self.info_dict['running_end'] = event_hash_id
        self._update_info()

    # 设置deadline

    # 删除开始定时器
    def del_start_scheduler(self):
        hash_id = "{sid}_start".format(sid=self.sid)
        Scheduler.remove_job(job_id=hash_id)

    # 删除结束定时器
    def del_end_scheduler(self):
        hash_id = "{sid}_end".format(sid=self.sid)
        Scheduler.remove_job(job_id=hash_id)

    # 更新tree信息
    def _update_info(self):
        print("update tree")
        print(self.info_dict)
        tree_obj = CronProgramVersionTree.objects(hash_id=self.info_dict['hash_id'])
        tree_obj.update(**self.info_dict)

    # 更新定时器
    def update_dead_line(self):
        self.del_dead_line_scheduler()

    # 删除定时器
    def del_dead_line_scheduler(self):
        self.del_end_scheduler()
        self.del_start_scheduler()

