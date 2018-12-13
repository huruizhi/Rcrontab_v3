from master_server.models import PyScriptBaseInfoV2, TablesInfo, Path
from master_server.cal_obj_lib.cal_obj import CalObj
import json
from time import sleep
import os
import threading


class MaintainCalProgram:
    _instance_lock = threading.Lock()

    def __init__(self):
        self.cal_program_obj_dic = dict()
        self.tmp_file = os.path.dirname(os.path.abspath(__file__)) + '/.cal_info.tmp'

        self.programs_info = self.read_from_tmp()
        if not self.programs_info:
            self.programs_info = self._get_plan()

        for sid in self.programs_info:
            self.cal_program_obj_dic[str(sid)] = CalObj(**self.programs_info[sid])

        self.write_to_tmp()

    def __new__(cls, *args, **kwargs):
        if not hasattr(MaintainCalProgram, "_instance"):
            with MaintainCalProgram._instance_lock:
                if not hasattr(MaintainCalProgram, "_instance"):
                    MaintainCalProgram._instance = object.__new__(cls)
        return MaintainCalProgram._instance

    # 从mysql数据库读取 所有程序 计划任务信息
    @staticmethod
    def _get_plan():
        programs_info_new = dict()

        # 查找计算程序
        programs = PyScriptBaseInfoV2.objects.filter(program_type=1).filter(is_stop=0)

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

            # 获取变量
            sid = program.sid
            path = Path.objects.get(program=program).path
            api = path + program.name

            program_info = {'sid': sid, 'pre_tables': pre_tables_list, 'result_tables': result_tables_list,
                            'api': api}
            programs_info_new[str(sid)] = program_info
        return programs_info_new

    # loop check 信息表
    def loop_check_table(self):
        while True:
            self.programs_info = self._get_plan()

            for sid in self.programs_info:
                sid_str = str(sid)
                if sid_str not in self.cal_program_obj_dic:
                    self.cal_program_obj_dic[sid_str] = CalObj(**self.programs_info[sid])
                    self.write_to_tmp()
                else:
                    if_fresh = self.cal_program_obj_dic[sid_str].refresh(**self.programs_info[sid])
                    if if_fresh:
                        self.write_to_tmp()
            sleep(20)

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




