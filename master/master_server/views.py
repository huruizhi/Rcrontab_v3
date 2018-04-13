from django.shortcuts import HttpResponse
from django.views import View
from master_server.maintain_programs import MaintainProgram
from master_server.Loop_check_program_result_log import LoopReadResultLog
from master_server.mail_failed_log import SendFailedLog
from threading import Thread
from time import sleep
# Create your views here.


class ServerStart(View):
    def get(self, request):
        programs = MaintainProgram()
        threads = list()
        threads.append(Thread(target=LoopReadResultLog().loop_read_log))
        threads.append(Thread(target=SendFailedLog().start))
        for thread in threads:
            thread.start()
        return HttpResponse('OK')
