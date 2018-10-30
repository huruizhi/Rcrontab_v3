from threading import Thread
from datetime import date
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.jobstores.sqlalchemy import SQLAlchemyJobStore
from apscheduler.executors.pool import ThreadPoolExecutor
from urllib import request
from apscheduler import events
import pytz
import time
import logging
from slave_server.log_module import write_log


def _get_url(sid, url):
    try:
        parameter_str = "?sid={sid}&version={version}&subversion={subversion}".format(sid=sid, version=date.today(),
                                                                                      subversion=int(time.time())*1000)
        url = url+parameter_str
        req = request.Request(url)
        page = request.urlopen(req).read()
        write_log.info("url:{url}\nresult:{page}".format(url=url, page=page))
    except Exception as e:
        write_log.error("url:{url}\nerror:{err}".format(url=url, err=e))


class _Scheduler:
    def __init__(self):
        job_store = SQLAlchemyJobStore(url='sqlite:///jobs.sqlite')
        jobs_stores = {
            'default': job_store,
        }

        executors = {
            'default': ThreadPoolExecutor(50),
        }
        tz = pytz.timezone('Asia/Shanghai')
        self._scheduler = BackgroundScheduler(jobstores=jobs_stores, time_zone=tz, executors=executors)
        thread = Thread(target=self._scheduler.start)
        thread.start()
        self._scheduler.add_listener(self.my_listener, events.EVENT_ALL)

    def add_job_url(self, sid, url, cron_str):
        minute, hour, day, month, day_of_week = cron_str.split()
        if day_of_week in ['7', '07']:
            day_of_week = '0'
        self._scheduler.add_job(_get_url, 'cron', args=(sid, url), minute=minute,
                                hour=hour, day=day, month=month, day_of_week=day_of_week,
                                id=str(sid), name=str(sid), replace_existing=True, misfire_grace_time=300)

    def remove_job(self, sid):
        self._scheduler.remove_job(str(sid))

    def get_job(self, sid):
        return self._scheduler.get_job(job_id=str(sid))

    def get_jobs(self):
        return self._scheduler.get_jobs()

    def pause_job(self, sid):
        self._scheduler.pause_job(job_id=str(sid))

    def resume_job(self, sid):
        self._scheduler.resume_job(job_id=str(sid))

    @staticmethod
    def my_listener(event):
        logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')


Scheduler = _Scheduler()

if __name__ == '__main__':
    url_1 = "http://192.168.0.157:3552/bond_v2/bond/PyBondIndexRateData21"
    _get_url(sid=401, url=url_1)

