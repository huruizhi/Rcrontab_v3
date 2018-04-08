from django.shortcuts import HttpResponse
from django.views import View
import json
from slave_server.schedulers import Scheduler
# Create your views here.


class HoldConnection(View):

    def get(self, request):
        print(request.GET)
        if 'info' in request.GET:
            if request.GET['info'] == 'hello':
                return HttpResponse('hello')
        else:
            return HttpResponse('')


class RevExecPlan(View):

    def post(self, request):
        print(request.post)
        if 'add_list' in request.post:
            err_string = ''
            add_list = json.loads(request.post['add_list'])
            for program in add_list:
                cron = program['crontab']
                api = program['path']
                sid = program['sid']
                try:
                    Scheduler.add_job_url(sid=sid, url=api, cron_str=cron)
                except Exception as e:
                    err_string = err_string+str(e)
                if err_string:
                    return HttpResponse(err_string)
                return HttpResponse('add success')

        if 'add_list' in request.post:
            err_string = ''
            add_list = json.loads(request.post['add_list'])
            for program in add_list:
                cron = program['crontab']
                api = program['path']
                sid = program['sid']
                try:
                    Scheduler.remove_job(sid=sid)
                    Scheduler.add_job_url(sid=sid, url=api, cron_str=cron)
                except Exception as e:
                    err_string = err_string+str(e)
                if err_string:
                    return HttpResponse(err_string)
                return HttpResponse('modify success')

        if 'del_list' in request.post:
            del_list = json.loads(request.post['del_list'])
            err_string = ''
            for sid in del_list:
                try:
                    Scheduler.remove_job(sid=sid)
                except Exception as e:
                    err_string = err_string+str(e)
            if err_string:
                return HttpResponse(err_string)
            return HttpResponse('del success')
        else:
            return HttpResponse('bad info!')


class GetExecPlan(View):
    def get(self, request, sid=None):
        if sid is None:
            return HttpResponse(Scheduler.get_jobs())
        else:
            try:
                return HttpResponse(Scheduler.get_job(sid=sid))
            except Exception as e:
                return HttpResponse(str(e))
