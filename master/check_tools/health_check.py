import os
import django
from check_tools import tools
from master_server import mongo_models as mo
from master_server import models as m
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "master.settings")
django.setup()
import datetime


def check_cal_run_miss_start():
    p = m.PyScriptBaseInfoV2.objects.filter(program_type=1)
    not_in_sql = list()
    not_run = list()
    for i in p:
        try:
            cal_p_tree = tools.get_cal_tree(i.pk, 1)
            if cal_p_tree.status == 4:
                not_in_sql.append(i.pk)
        except Exception as e:
            not_run.append(i.pk)
    print(not_in_sql)
    print(not_run)


def check_cal_res():
    cal = mo.CalProgramInfo.objects.all()
    for c_p in cal:
        pointer = c_p.pointer
        c_t = mo.CalVersionTree.objects.get(hash_id=pointer)
        pre_version = c_t.pre_version
        c_t_p = mo.CalVersionTree.objects.get(hash_id=pre_version)
        if c_t_p.status != 2:
            print(c_t_p.to_json())
            p_info = m.PyScriptBaseInfoV2.objects.get(sid=c_t_p.sid)
            print(p_info.name)
            print(p_info.owner)


class CalRunMissed:
    def __init__(self):
        cal = mo.CalProgramInfo.objects.all()
        self.cal_version_info = list()
        for c_p in cal:
            pointer = c_p.pointer
            c_t = mo.CalVersionTree.objects.get(hash_id=pointer)
            pre_version = c_t.pre_version
            try:
                self.cal_version_info.append((c_t, mo.CalVersionTree.objects.get(hash_id=pre_version)))
            except Exception as e:
                pass
        self.end_time = datetime.datetime.now() - datetime.timedelta(hours=24)

    def check_cal_run_missed(self):
        """
        检查未执行的计算程序
        :return:
        """
        try:
            i = 0
            for c_t, c_v_t in self.cal_version_info:
                e = mo.EventsHub.objects.get(hash_id=c_v_t.running_start)
                start_time = e.occur_datetime
                if start_time < self.end_time:
                    i = i+1
                    print("""{num}======
    开始时间            :{start_time}
    最新version信息     :{version_info_new}
    pre_version信息     :{version_info_pre}""".format(num=i, start_time=start_time,
                                                    version_info_new=c_t.to_json(), version_info_pre=c_v_t.to_json()))
        except Exception as e:
            print(123)


if __name__ == '__main__':
    cal = CalRunMissed()
    cal.check_cal_run_missed()
