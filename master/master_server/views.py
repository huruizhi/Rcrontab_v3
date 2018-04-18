from django.shortcuts import HttpResponse
from django.views import View
# Create your views here.


class ServerStart(View):
    def get(self, request):
        return HttpResponse('OK')
