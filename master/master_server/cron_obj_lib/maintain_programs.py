from master_server.models import PyScriptBaseInfoV2, TablesInfo, ServerInfo, Path
from master_server.cron_obj_lib.cron_obj import CronObj
import json
from time import sleep
import os
import threading


class MaintainPrograms:
    _instance_lock = threading.Lock()

    def __init__(self):
        self.cron_program_obj_dic = dict()
        self.tmp_file = os.path.dirname(os.path.abspath(__file__)) + '/.cron_info.tmp'

        self.programs_info = self.read_from_tmp()
        if not self.programs_info:
            self.programs_info = self._get_plan()
            self.write_to_tmp()

        for sid in self.programs_info:
            self.cron_program_obj_dic[str(sid)] = CronObj(**self.programs_info[sid])

    def __new__(cls, *args, **kwargs):
        if not hasattr(MaintainPrograms, "_instance"):
            with MaintainPrograms._instance_lock:
                if not hasattr(MaintainPrograms, "_instance"):
                    MaintainPrograms._instance = object.__new__(cls)
        return MaintainPrograms._instance

    # 从mysql数据库读取 所有程序 计划任务信息
    @staticmethod
    def _get_plan():
        programs_info_new = dict()
        programs = PyScriptBaseInfoV2.objects.filter(program_type=0).filter(is_stop=0)
        for program in list(programs):

            # 获取结果表列表
            result_tables = TablesInfo.objects.filter(father_program=program)
            result_tables_list = []
            for result_table in result_tables:
                result_tables_list.append(result_table.pk)

            # 获取前置表列表
            pre_tables = TablesInfo.objects.filter(son_program=program)
            pre_tables_list = []
            for pre_table in pre_tables:
                pre_tables_list.append(pre_table.pk)
            server_id = ServerInfo.objects.get(path__program=program).pk

            # 获取变量
            cron = program.cron
            sid = program.sid
            path = Path.objects.get(program=program).path
            api = path + program.name

            program_info = {'sid': sid, 'pre_tables': pre_tables_list, 'result_tables': result_tables_list,
                            'cron': cron, 'api': api, 'server_id': server_id}
            programs_info_new[str(sid)] = program_info
        return programs_info_new

    # loop check 信息表
    def loop_check_table(self):
        while True:
            cron_program_info_dict = self._get_plan()

            for sid in cron_program_info_dict:
                sid = str(sid)
                if sid not in self.cron_program_obj_dic:
                    self.cron_program_obj_dic[sid] = CronObj(**cron_program_info_dict[sid])
                else:
                    self.cron_program_obj_dic[sid].refresh(**cron_program_info_dict[sid])
            sleep(30)

    # 将计划任务信息 从 缓存文件 中读取出来
    def read_from_tmp(self):
        programs_info = {}
        if not os.path.isfile(self.tmp_file):
            open(self.tmp_file, 'w')
            return programs_info

        # 从文件中获取缓存信息
        with open(self.tmp_file, 'r') as f:
            while True:
                program_info_encode = f.readline()
                if not program_info_encode:
                    break
                pass  # do something

                program_info = json.loads(program_info_encode)
                sid = program_info['sid']
                programs_info[sid] = program_info
            return programs_info

    # 将计划任务信息 写入 缓存文件
    def write_to_tmp(self):
        with open(self.tmp_file, 'w') as f:
            for sid in self.programs_info:
                program_info = self.programs_info[sid]
                program_info_encode = json.dumps(program_info)
                f.write(program_info_encode+'\n')

    def delete_obj(self, sid):
        if str(sid) in self.cron_program_obj_dic:
            self.cron_program_obj_dic[str(sid)].delete_obj()
            del self.cron_program_obj_dic[str(sid)]
            base_obj = PyScriptBaseInfoV2.objects.get(sid=int(sid))
            base_obj.is_stop = 1
            base_obj.save()

            # 重写临时配置文件
        if int(sid) in self.programs_info:
            del self.programs_info[int(sid)]
            self.write_to_tmp()
            return True
        else:
            return False

    def send_exec_plan(self):
        for _, cron in self.cron_program_obj_dic.items():
            cron.cron_info_obj.send_exec_plan()
<<<<<<< HEAD
=======

>>>>>>> rewrit_table_module
