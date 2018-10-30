from django.shortcuts import HttpResponse
from django.views import View
from slave_server.schedulers import Scheduler
# Create your views here.
from urllib import request as rt
from service_start import ThreadManage


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


class ExecuteApi(View):
    def post(self, request):
        url = request.POST['url']
        page = ''
        try:
            req = rt.Request(url)
            page = rt.urlopen(req, timeout=10).read()
            page = page.decode('utf-8')
        except Exception as e:
            page = str(e)
        finally:
            return HttpResponse(page)


class ServerStart(View):
    """
    启动程序
    """
    def get(self, request):
        result = ThreadManage.begin()
        if result:
            return HttpResponse("server start successful!")
        else:
            return HttpResponse("server has started!")


class CheckStatus(View):
    """
    检查程序状态
    """
    def get(self, request, info_type):
        if info_type == "send_mail":
            check_mail = ThreadManage.check_mail()
            check_mail_str = '<br>'.join(check_mail)
            return HttpResponse(check_mail_str)
        elif info_type == "threads":
            resp = ThreadManage.check()
            return HttpResponse(resp, content_type="application/json")
