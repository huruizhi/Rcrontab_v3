from slave_server.schedulers import Scheduler
from time import sleep
from apscheduler import events
program_sid = 1
program_cron_str_1 = '* * * * *'
program_cron_str_2 = '*/2 * * * *'


def my_listener(event):
    print(event.job_id)
    print(event.scheduled_run_times[0].strftime("%Y-%m-%d %H:%M:%S"))
    print(Scheduler.get_job(event.job_id).next_run_time.strftime("%Y-%m-%d %H:%M:%S"))
    print(Scheduler.get_job(event.job_id).trigger)


Scheduler._scheduler.add_listener(my_listener, events.EVENT_ALL)





