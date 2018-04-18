"""master URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/2.0/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path, include
from master_server.maintain_programs import MaintainProgram
from master_server.Loop_check_program_result_log import LoopReadResultLog
from master_server.mail_failed_log import SendFailedLog
# from multiprocessing import Process
from threading import Thread

urlpatterns = [
    path('admin/', admin.site.urls),
    path('master_server/', include('master_server.urls'))
]


def get_start():
    programs = MaintainProgram()
    threads = list()
    threads.append(Thread(target=SendFailedLog().start))
    threads.append(Thread(target=LoopReadResultLog().loop_read_log))

    for thread in threads:
        thread.start()


# get_start()
