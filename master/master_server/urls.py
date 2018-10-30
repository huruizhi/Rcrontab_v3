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
from django.urls import path
from master_server.views import *

app_name = 'master_server'
urlpatterns = [
    path('check_status/<info_type>/', CheckStatus.as_view()),
    path('get_plan/<job_id>/', GetExecPlan.as_view()),
    path('get_plan/', GetExecPlan.as_view()),
    path('del_plan/', DelExecPlan.as_view()),
    path('start/', ServerStart.as_view()),
    path('add_program/', AddProgramApi.as_view(), name='insert'),
    path('send_plan/', SendExecPlan.as_view()),
    path('program/status/<option>/', ProgramStatusCheck.as_view()),
    path('slave_program_result/', SlaveProgramResult.as_view()),
    path('sync_result/', SyncResult.as_view())
]
