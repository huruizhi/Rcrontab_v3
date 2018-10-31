from django.shortcuts import HttpResponse, render
from django.views import View
import json
from master_server.cron_obj_lib.maintain_programs import MaintainProgram
from master_server.schedulers.schedulers import Scheduler
from sevice_start import ThreadManage
from master_server.packages.read_program_base_info import ReadProgramsInfo
from . import forms
from check_tools.get_hist_info import GetHistInfo
from check_tools.get_parent_son import ParenSonInfo
from master_server.packages.slave_program_result_log import SlaveResultLog
from master_server.packages.mysql_sync_result import MysqlSyncLog
from master_server.packages.log_module import result_reader

from check_tools.get_cal_info import GetCalInfo
# Create your views here.


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


class GetExecPlan(View):
    """
    获取计划任务
    """
    def get(self, request, job_id=None):
        if job_id is None:
            return HttpResponse(Scheduler.get_jobs())
        else:
            try:
                response = "Scheduler: {scheduler}".format(scheduler=Scheduler.get_job(job_id=job_id))
                return HttpResponse(response)
            except Exception as e:
                return HttpResponse(str(e))


class DelExecPlan(View):
    """
    删除执行计划任务
    """
    def get(self, request):
        if 'sid' in request.GET:
            sid = request.GET['sid']
            print(sid)
            if MaintainProgram.delete_obj(sid=sid):
                return HttpResponse("cron_program:{sid} delete successful!".format(sid=sid))
            else:
                return HttpResponse("cron_program:{sid} is not in schedulers!".format(sid=sid))


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


class AddProgramApi(View):
    """
    添加执行程序
    """
    def post(self, request):
        form = forms.ConfigFileLogForm(request.POST, request.FILES)
        print("Post:", request.POST)
        print("file_name:", request.FILES)
        if form.is_valid():
            # file is saved
            configfile = form.save()
            info = ReadProgramsInfo(configfile).get_programs_info_list()
            return HttpResponse(info)
        else:
            info = form.errors
            print(info)
        return render(request, 'rcrontab_formals/insert.html', {'form': form})

    def get(self, request):
        form = forms.ConfigFileLogForm()
        return render(request, 'rcrontab_formals/insert.html', {'form': form})


class SendExecPlan(View):
    """
    手动发送执行计划给slave
    """
    def get(self, request):
        try:
            MaintainProgram.send_exec_plan()
            page = 'send exec plan ok!'
        except Exception as e:
            page = str(e)
        finally:
            return HttpResponse(page)


class ProgramStatusCheck(View):
    def get(self, request, option):
        if option == 'hist_info':
            sid = request.GET['sid']
            pre = request.GET['pre'] if 'pre' in request.GET else None
            hist_info = GetHistInfo(sid, pre)
            return HttpResponse(hist_info(), content_type="application/json")
        if option == 'parent_son':
            sid = request.GET['sid']
            ps = ParenSonInfo(sid)
            return HttpResponse(json.dumps(ps(), ensure_ascii=False), content_type="application/json")


class SlaveProgramResult(View):
    def post(self, request):
        msg = request.POST['result']
        result_reader.info('=====debug=====')
        result_reader.info(msg)
        result_reader.info('===============')
        try:
            slave_msg = SlaveResultLog(msg)
            slave_msg.input_msg()
            return HttpResponse("OK")
        except Exception as e:
            return HttpResponse("Error")


class SyncResult(View):
    def post(self, request):
        msg = request.POST['result']
        result_reader.info('=====debug=====')
        result_reader.info(msg)
        result_reader.info('===============')
        try:
            MysqlSyncLog(msg)
            return HttpResponse("OK")
        except Exception as e:
            return HttpResponse("Error")


class GetCalResult(View):
    def get(self, request, pk=None):
        g = GetCalInfo(pk)
        return HttpResponse(g())

