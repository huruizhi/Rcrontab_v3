from threading import Thread
from apscheduler.schedulers.blocking import BlockingScheduler
from apscheduler.jobstores.sqlalchemy import SQLAlchemyJobStore
import pytz
from master_server.collect_info_to_mq import SendProgramStatus
from master_server.packages.hash import get_hash
from datetime import datetime
from time import sleep
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


def _get_url():
    pass


def send_program_status(sid, status, subversion=None):
    occur_datetime = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    if status == 'start':
        msg_type = 4
        info = '{sid}: Running miss start'.format(sid=sid)
        info_dict = {'sid': sid, 'type': msg_type, 'info': info, 'occur_datetime': occur_datetime}
    elif status == 'end':
        msg_type = 5
        info = '{sid}: Not back the end status to Mysql database!'.format(sid=sid)
        info_dict = {'sid': sid, 'type': msg_type, 'info': info,
                     'occur_datetime': occur_datetime, 'subversion': subversion}
    else:
        return
    hash_id = get_hash(info_dict)
    info_dict['hash_id'] = hash_id
    sent_status = SendProgramStatus(message=info_dict, msg_type='program')
    for i in range(10):
        result = sent_status.send_msg()
        if result:
            break
        sleep(20)


class _Scheduler:
    def __init__(self):
        job_store = SQLAlchemyJobStore(url='sqlite:///jobs.sqlite')
        jobs_stores = {
            'default': job_store,
        }
        tz = pytz.timezone('Asia/Shanghai')
        self._scheduler = BlockingScheduler(jobstores=jobs_stores, time_zone=tz)
        thread = Thread(target=self._scheduler.start)
        thread.start()

    def add_job_info(self, sid, cron_str):
        minute, hour, day, month, day_of_week = cron_str.split()
        if day_of_week == '7' or day_of_week == '07':
            day_of_week = '0'
        self._scheduler.add_job(_get_url, 'cron', minute=minute,
                                hour=hour, day=day, month=month, day_of_week=day_of_week,
                                id=str(sid)[0:5], name=str(sid)[0:5], replace_existing=True)

    def add_job_deadline(self, cron_tree_hash, date_time, sid, status, subversion=None):
        if status in ['start', 'end']:
            self._scheduler.add_job(send_program_status, 'date', run_date=date_time, id=cron_tree_hash,
                                    name="{sid}: {status} deadline".format(sid=sid, status=status),
                                    args=[sid, status, subversion])

    def remove_job(self, job_id):
        self._scheduler.remove_job(str(job_id))

    def get_job_next_run_time(self, job_id):
        return self._scheduler.get_job(job_id).next_run_time

    def pause_job(self, job_id):
        self._scheduler.pause_job(job_id=str(job_id))

    def resume_job(self, job_id):
        self._scheduler.resume_job(job_id=str(job_id))


Scheduler = _Scheduler()

if __name__ == '__main__':
    url_1 = "http://192.168.0.157:3502/bond_v2/bond/PyBondShanghaiExchangeBaseInfo21"

