from django.shortcuts import HttpResponse
from django.views import View
import json
from slave_server.schedulers import Scheduler
# Create your views here.
API = dict()


class HoldConnection(View):

    def get(self, request):
        print(request.GET)
        if 'info' in request.GET:
            if request.GET['info'] == 'hello':
                return HttpResponse('hello')
        else:
            return HttpResponse('')


class RevExecPlan(View):

    def post(self, request, action):
        if action == 'add':
            err_string = ''
            cron = request.POST['cron']
            api = request.POST['api']
            sid = request.POST['sid']
            API[sid] = api
            try:
                Scheduler.add_job_url(sid=sid, url=api, cron_str=cron)
            except Exception as e:
                err_string = err_string+str(e)
            if err_string:
                return HttpResponse(err_string)
            return HttpResponse('add success')

        if action == 'mod':
            err_string = ''
            cron = request.POST['cron']
            api = request.POST['api']
            sid = request.POST['sid']
            try:
                Scheduler.remove_job(sid=sid)
                Scheduler.add_job_url(sid=sid, url=api, cron_str=cron)
            except Exception as e:
                err_string = err_string+str(e)
            if err_string:
                return HttpResponse(err_string)
            return HttpResponse('modify success')

        if action == 'del':
            err_string = ''
            try:
                sid = request.POST['sid']
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
                response = "API:{api} \n Scheduler: {scheduler}".format(api=API[sid],
                                                                        scheduler=Scheduler.get_job(sid=sid))
                return HttpResponse(response)
            except Exception as e:
                return HttpResponse(str(e))
