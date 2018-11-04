from threading import Thread
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.jobstores.sqlalchemy import SQLAlchemyJobStore
import pytz
from master_server.collect_info_to_mq import SendProgramStatus
from apscheduler.executors.pool import ThreadPoolExecutor
from master_server.packages.hash import get_hash
from datetime import datetime
from time import sleep
from django.db import connection
from master_server.packages.log_module import scheduler_log
from master_server.packages.quality_control_new import QualityControl



'''
    hash_id = mn.StringField(max_length=16, required=True, Unique=True)
    sid = mn.IntField()
    tid = mn.IntField()
    type = mn.IntField(choices=events_type)
    info = mn.StringField()
    version = mn.DateTimeField()
    subversion = mn.DateTimeField()
    occur_datetime = mn.DateTimeField()
'''


# def _get_url(sid):
#     # 设置五分钟为超时时间
#     date_time = datetime.now() + timedelta(minutes=5)
#     hash_id = "{sid}_start".format(sid=sid)
#     Scheduler.add_job_deadline(cron_tree_hash=hash_id, date_time=date_time, status='start', sid=sid)
#
#     date_time = datetime.now() + timedelta(hours=3)
#     hash_id = "{sid}_end".format(sid=sid)
#     Scheduler.add_job_deadline(cron_tree_hash=hash_id, date_time=date_time, status='end', sid=sid)


# 超时事件发送
def send_program_status(sid, status, subversion=None):
    occur_datetime = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    if status == 'start':
        msg_type = 4
        info = '{sid}: Running miss start'.format(sid=sid)
        info_dict = {'sid': sid, 'type': msg_type, 'info': info, 'occur_datetime': occur_datetime,
                     'source': 'apscheduler'}
    elif status == 'end':
        if not subversion:
            subversion = occur_datetime
        msg_type = 5
        info = '{sid}: Not end status in Mysql database!'.format(sid=sid)
        info_dict = {'sid': sid, 'type': msg_type, 'info': info,
                     'occur_datetime': occur_datetime, 'subversion': subversion, 'source': 'apscheduler'}
    else:
        return
    hash_id = get_hash(info_dict)
    info_dict['hash_id'] = hash_id
    sent_status = SendProgramStatus(message=info_dict, msg_type='p')
    for i in range(10):
        result = sent_status.send_msg()
        if result:
            break
        sleep(20)


# # 人工输入表插入table_events exchange
# def manual_update_table_events():
#     if not is_connection_usable():
#         connection.close()
#
#     # 刷新表
#     update_table_data_source()
#     tables = TablesInfo.objects.filter(data_source=1).filter(db_server='db_153')
#     tables_list = list()
#
#     for t in tables:
#         tables_list.append(t.pk)
#     for tid in tables_list:
#         occur_datetime = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
#         version = datetime.now().strftime('%Y-%m-%d')
#         event_info = {'tid': tid, 'type': 103,
#                       'info': 'manual_table_with_out QC',
#                       'occur_datetime': occur_datetime,
#                       'version': version,
#                       'source': "manual_update"}
#         hash_id = get_hash(event_info)
#         event_info['hash_id'] = hash_id
#         SendProgramStatus(message=event_info, msg_type='t').send_msg()


def update_table_data_source():

    sql1 = '''
    UPDATE
    py_script_tables_info
    set
    data_source=1
            '''
    sql2 = '''
    update 
    py_script_tables_info a
    LEFT join
    (select DISTINCT tablesinfo_id  from py_script_base_info_v2_result_tables) b
    on a.id = b.tablesinfo_id
    SET data_source=0
    where b.tablesinfo_id is not null'''
    cursor = connection.cursor()
    cursor.execute(sql1)
    cursor.execute(sql2)


# 数据库连接检查
def is_connection_usable():
    try:
        connection.connection.ping()
    except Exception as e:
        return False
    else:
        return True


class SchedulerLib:
    def __init__(self):
        jobstores = {
            'default': SQLAlchemyJobStore(url='sqlite:///jobs.sqlite'),
        }
        executors = {
            'default': ThreadPoolExecutor(50),
        }
        tz = pytz.timezone('Asia/Shanghai')
        self._scheduler = BackgroundScheduler(jobstores=jobstores, time_zone=tz, executors=executors)
        self._scheduler.remove_all_jobs()
        qc = QualityControl()
        self._scheduler.add_job(qc, 'cron', minute='30',
                                hour='08', day='*', month='*', day_of_week='*',
                                id=str('QualityControl'), name=str('QualityControl'),
                                replace_existing=True, misfire_grace_time=300)

        thread = Thread(target=self._scheduler.start)
        thread.start()

    def add_job_info(self, sid, cron_str):
        try:
            minute, hour, day, month, day_of_week = cron_str.split()
            if day_of_week == '7' or day_of_week == '07':
                day_of_week = '0'
            self._scheduler.add_job(_get_url, 'cron', minute=minute,
                                    hour=hour, day=day, month=month, day_of_week=day_of_week,
                                    id=str(sid), name=str(sid), args=[sid, ], replace_existing=True, misfire_grace_time=300)
        except Exception as e:
            print(__name__ + ":" + str(sid))
            print(e)

    def add_job_deadline(self, cron_tree_hash, date_time, sid, status, subversion=None):
        if status in ['start', 'end']:
            try:
                self._scheduler.remove_job(job_id=cron_tree_hash)
            except Exception as e:
                pass
            finally:
                scheduler_log.info('add sid:{sid} status:{status} '.format(sid=sid, status=status))
                self._scheduler.add_job(send_program_status, 'date', run_date=date_time, id=cron_tree_hash,
                                        name="{sid}: {status} deadline".format(sid=sid, status=status),
                                        args=[sid, status, subversion], replace_existing=True)

    # def add_manual_update_table(self):
    #     self._scheduler.add_job(manual_update_table_events, 'cron', minute='00',
    #                             hour='20', day='*', month='*', day_of_week='*',
    #                            id='manual', name='manual_update_table', replace_existing=True, misfire_grace_time=300)

    def remove_job(self, job_id):
        try:
            scheduler_log.info('del job_id:{job_id}'.format(job_id=job_id))
            self._scheduler.remove_job(str(job_id))
        except Exception as e:
            scheduler_log.info('del err job_id:{job_id}'.format(job_id=job_id))

    def get_job_next_run_time(self, job_id):
        return self._scheduler.get_job(job_id).next_run_time

    def pause_job(self, job_id):
        self._scheduler.pause_job(job_id=str(job_id))

    def resume_job(self, job_id):
        self._scheduler.resume_job(job_id=str(job_id))

    def get_jobs(self):
        return self._scheduler.get_jobs()

    def get_job(self, job_id):
        return self._scheduler.get_job(job_id=job_id)


if __name__ == '__main__':
    url_1 = "http://192.168.0.157:3502/bond_v2/bond/PyBondShanghaiExchangeBaseInfo21"

