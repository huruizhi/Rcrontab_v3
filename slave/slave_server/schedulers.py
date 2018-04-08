from threading import Thread
from datetime import date
from apscheduler.schedulers.blocking import BlockingScheduler
from apscheduler.jobstores.sqlalchemy import SQLAlchemyJobStore
from urllib import request
import pytz


def _get_url(sid, url):
    parameter_str = "?sid={sid}&version={version}".format(sid=sid, version=date.today())
    url = url+parameter_str
    req = request.Request(url)
    page = request.urlopen(req).read()


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

    def add_job_url(self, sid, url, cron_str):
        minute, hour, day, month, day_of_week = cron_str.split()
        self._scheduler.add_job(_get_url, 'cron', args=(sid, url), minute=minute,
                                hour=hour, day=day, month=month, day_of_week=day_of_week,
                                id=str(sid), name=str(sid), replace_existing=True)

    def remove_job(self, sid):
        self._scheduler.remove_job(str(sid))

    def get_job(self, sid):
        return self._scheduler.get_job(job_id=sid)

    def get_jobs(self):
        return self._scheduler.get_jobs()

    def pause_job(self, sid):
        self._scheduler.pause_job(job_id=str(sid))

    def resume_job(self, sid):
        self._scheduler.resume_job(job_id=str(sid))


Scheduler = _Scheduler()

if __name__ == '__main__':
    url_1 = "http://192.168.0.157:3502/bond_v2/bond/PyBondShanghaiExchangeBaseInfo21?sid=402&version={version}"
    Scheduler.add_job_url(sid=1, url=url_1, cron_str='10 22 * * *')
    #Scheduler.remove_job(sid=1)
    print(Scheduler.get_job(sid=1))

