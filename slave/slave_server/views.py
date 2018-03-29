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
            add_list = json.loads(request.post['add_list'])
            for program in add_list:
                cron = program['crontab']
                api = program['path']
                sid = program['sid']
                Scheduler.add_job_url(sid=sid, url=api, cron_str=cron)
        if 'del_list' in request.post:
            del_list = json.loads(request.post['del_list'])
            for sid in del_list:
                Scheduler.remove_job(sid=sid)

        else:
            return HttpResponse('bad info!')




class GetCommand:

    def __init__(self, program_info):
        self.program_info = program_info
        self.sid = program_info['sid']
        self.program = program_info['path']
        self.run_type = program_info['run_type']

    def __call__(self, *args, **kwargs):
        if self.run_type == 1:
            return self._exec_program()
        else:
            return self._url_program()

    def _url_program(self):
        parameter_str = "?sid={sid}&version={date}"
        get_url = "curl  " + self.program + parameter_str
        return get_url

    def _exec_program(self):
        if os.path.splitext(self.program)[1] == '.jar':
            get_cmd = "java  -jar" + self.program
        elif os.path.splitext(self.program)[1] == '.sh':
            get_cmd = "sh " + self.program
        elif os.path.splitext(self.program)[1] == '.py':
            get_cmd = "python -u " + self.program
        else:
            get_cmd = "%{program} 程序类型仅支持 shell(.sh) python(.py) java(.jar)".format(program=self.program)
        return get_cmd
