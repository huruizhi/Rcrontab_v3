from master_server.mongo_models import CronProgramInfo
from master_server.models import ServerInfo
from urllib import request, parse
from check_tools.tools import slave_exec_api
from sevice_start import ThreadManage
Scheduler = ThreadManage.Scheduler
from datetime import datetime


class CronInfoObj:
    def __init__(self, sid, pre_tables, result_tables, cron, api, server_id, hash_ack):
        self.sid = sid
        self.info_dict = self.get_info_from_mongodb()
        info_dict_new = {'sid': sid, 'result_tables': result_tables, 'pre_tables': pre_tables,
                         'cron': cron, 'api': api, 'server_id': server_id, 'hash_ack': hash_ack}
        # Scheduler.add_job_info(sid=self.sid, cron_str=self.info_dict['cron'])

        # mongodb中不存在项目信息，说明是新项目
        if not self.info_dict:
            # 创建空指针
            info_dict_new['pointer'] = ''
            self.info_dict = info_dict_new
            self.write_info_to_mongodb()
            self.send_exec_plan()

        # 项目信息更改
        elif self.info_dict['hash_ack'] != hash_ack:
            self.update_info_to_mongodb(**info_dict_new)
            self.info_dict = self.get_info_from_mongodb()
            self.send_exec_plan()
        else:
            self.send_exec_plan()

        # Info指针
        self.pointer = self.info_dict['pointer']

        # 部署服务器修改
        if server_id != self.info_dict['server_id']:
            self.drop_exec_plan()
            self.update_info_to_mongodb(**{'server_id': server_id})
            self.send_exec_plan()

        # # 将程序加入定时器
        Scheduler.add_job_info(sid=self.sid, cron_str=self.info_dict['cron'])

    def exec_api(self):
        date_today = datetime.now()
        date_today = date_today.strftime('%Y-%m-%d')
        status, result = slave_exec_api(self.sid, date_today, subversion=True)
        if status is True:
            

    # 数据改变
    def info_change(self,  sid, pre_tables, result_tables, cron, api, hash_ack):
        info_dict_new = {'sid': sid, 'result_tables': result_tables, 'pre_tables': pre_tables,
                         'cron': cron, 'api': api, 'hash_ack': hash_ack}
        self.update_info_to_mongodb(**info_dict_new)
        self.send_exec_plan()
        self.info_dict = self.get_info_from_mongodb()
        # 修改定时器
        Scheduler.remove_job(job_id=self.sid)
        Scheduler.add_job_info(sid=self.sid, cron_str=self.info_dict['cron'])

    # 部署服务器更改
    def server_change(self, server_id):
        self.drop_exec_plan()
        self.update_info_to_mongodb(**{'server_id': server_id})
        self.send_exec_plan()

    # 修改指针
    def change_pointer(self, pointer):
        try:
            self.pointer = pointer
            self.info_dict['pointer'] = self.pointer
            info_obj = CronProgramInfo.objects(sid=self.sid)
            print(self.info_dict['pointer'])
            info_obj.update(**self.info_dict)
        except Exception as e:
            print(e)

    # 将info写入mongodb
    def write_info_to_mongodb(self):
        cron_program = CronProgramInfo(**self.info_dict)
        cron_program.save()

    # 从mongodb读出数据
    def get_info_from_mongodb(self):
        info = dict()
        try:
            info_obj = CronProgramInfo.objects.get(sid=self.sid)
            # 转换成字典
            info = dict(info_obj.to_mongo())

            # 去掉Objectid
            info.pop('_id')
        except Exception as e:
            info = dict()
        finally:
            return info

    # 向mongodb更新信息
    def update_info_to_mongodb(self, **kwargs):
        info_obj = CronProgramInfo.objects(sid=self.sid)
        info_obj.update(**kwargs)
        self.info_dict = self.get_info_from_mongodb()

    # 发送任务到slave
    def send_exec_plan(self):
        try:
            ip, port = self.get_slave_net()
            url = 'http://{ip}:{port}/slave_server/set_plan/add/'.format(ip=ip, port=port)
            data = {'sid': self.sid, 'cron': self.info_dict['cron'], 'api': self.info_dict['api']}
            data = parse.urlencode(data).encode('utf-8')
            req = request.Request(url, data=data)
            page = request.urlopen(req).read()
            page = page.decode('utf-8')
        except Exception as e:
            print(e)

    # 删除salve任务
    def drop_exec_plan(self):
        try:
            ip, port = self.get_slave_net()
            url = 'http://{ip}:{port}/slave_server/set_plan/del/'.format(ip=ip, port=port)
            data = {'sid': self.sid}
            data = parse.urlencode(data).encode('utf-8')
            req = request.Request(url, data=data)
            page = request.urlopen(req).read()
            page = page.decode('utf-8')

        except Exception:
            page = 'error'
        return page

    def del_scheduler(self):
        try:
            Scheduler.remove_job(job_id=self.sid)
        except Exception:
            pass

    # 执行计划修改
    def modified_exec_plan(self):
        pass

    # 获取slave网络信息
    def get_slave_net(self):
        slave_info_obj = ServerInfo.objects.get(pk=self.info_dict['server_id'])
        slave_info_net = (slave_info_obj.ip, slave_info_obj.port)
        return slave_info_net





