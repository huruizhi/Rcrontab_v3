from django.shortcuts import HttpResponse
from django.views import View
from master_server.maintain_programs import MaintainProgram

# Create your views here.


class ServerStart(View):
    def get(self, request):
        programs = MaintainProgram().maintain()
        return HttpResponse('OK')
