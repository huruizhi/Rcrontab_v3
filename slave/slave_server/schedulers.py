from threading import Thread
from datetime import date
from apscheduler.schedulers.blocking import BlockingScheduler
from apscheduler.jobstores.memory import MemoryJobStore
from urllib import request
import pytz


def _get_url(sid, url):
    parameter_str = "?sid={sid}&version={version}".format(sid=sid, version=date.today())
    url = url+parameter_str
    req = request.Request(url)
    page = request.urlopen(req).read()
    page = page.decode('utf-8')
    #print(page)


class _Scheduler:
    def __init__(self):
        self.job_store = MemoryJobStore()
        jobs_tores = {
            'default': self.job_store,
        }
        tz = pytz.timezone('Asia/Shanghai')
        self._scheduler = BlockingScheduler(jobstores=jobs_tores, time_zone=tz)
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
        return self._scheduler.get_job()


Scheduler = _Scheduler()

if __name__ == '__main__':
    url_1 = "http://192.168.0.157:3502/bond_v2/bond/PyBondShanghaiExchangeBaseInfo21?sid=402&version={version}"
    _get_url(url_1)

