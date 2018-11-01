from master_server import mongo_models as mm
import paramiko
from check_tools.tools import flush_program
import datetime


def _delete_mongo_data():
    mm_objs = [mm.EventsHub, mm.CalProgramInfo, mm.CalVersionTree,
               mm.TableInfo, mm.TableVersionTree,
               mm.CronProgramInfo, mm.CronProgramVersionTree, ]

    for mm_obj in mm_objs:
        for i in mm_obj.objects:
            i.delete()
    print("mongo delete successful!")


def _restart_docker():
    print("begin to restart docker")
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    ssh.connect(hostname="192.168.0.157", port=22, username="root", password="d!)iW@h1N)(j")
    stdin, stdout, stderr = ssh.exec_command('/bin/bash /script/rcrontab/restart_master.sh')
    result = stdout.read().decode()
    print(result)


def restart_server():
    _delete_mongo_data()
    _restart_docker()


if __name__ == "__main__":
    date_today = datetime.datetime.now()
    date_today = date_today.strftime('%Y-%m-%d')
    restart_server()
    flush_program(10, 23, date_today)





