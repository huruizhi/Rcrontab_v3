from django.conf import settings
from django.core.mail import send_mail
from master_server.packages.receive import ReceiveRabbitMQMessage
from master_server.models import PyScriptOwnerListV2, PyScriptBaseInfoV2, ServerInfo
from master_server.mongo_models import EventsHub
import json
from master_server.packages.log_module import WriteLog
from time import sleep
from django.db import connection


# 发送邮件
class SendFailedLog:
    def __init__(self):
        self.logging = WriteLog('send_mail')
        self.err_str = list()

    def start(self):
        self.logging.info('send_mall_connect_RabbitMQ')
        mq = ReceiveRabbitMQMessage(name='send_mail', target=self.send_mail)
        mq.start()

    def send_mail(self, ch, method, properties, body):
        if not is_connection_usable():
            connection.close()
        try:
            self.logging.info(body.decode('utf-8'))
            admin_mail = 'huruizhi@pystandard.com'
            log = json.loads(body.decode('utf-8'))
            if 'sid' in log:
                sid = log['sid']
                hash_id = log['hash_id']
                msg_type = int(log['type'])
                occur_datetime = log['occur_datetime']
                event_odj = EventsHub.objects.get(hash_id=hash_id)
                msg = event_odj.info

                server_info = ServerInfo.objects.get(path__program__sid=sid).name

                if int(msg_type) in [3, 4, 5]:
                    state = '失败'
                    owner_obj = PyScriptOwnerListV2.objects.get(programs__sid=int(sid))
                    mail = owner_obj.mail
                    program_obj = PyScriptBaseInfoV2.objects.get(sid=int(sid))
                    name = program_obj.name
                    path = program_obj.path.path
                    name = '{0}{1}'.format(path, name)
                    owner = owner_obj.owner
                    message = '''
sid:{sid}
责任人:{owner}
服务器信息:{server_info} 
说明：
    1.阿里云环境需要将域名更换为192.168.2.150进行接口调用
    2.内网环境直接使用域名调用
程序执行状态：{state}

产生时间：{occur_datetime}

程序日志信息：
{info}
                    
                    
                    '''.format(owner=owner, state=state, occur_datetime=occur_datetime, info=msg, sid=sid,
                               server_info= server_info)

                    title = '程序执行信息 - 接口：{name}'.format(name=name)

                    send_mail(title, message, settings.DEFAULT_FROM_EMAIL, [mail, admin_mail],)

                if int(msg_type) == 2:
                    state = '成功'
                    if msg:
                        if_send = 0
                        try:
                            msg_dict = json.loads(msg)
                            if type(msg_dict) == str:
                                if_send = 1
                            if type(msg_dict) == dict:
                                for i in msg_dict:
                                    if msg_dict[i]:
                                        if_send = 1
                                        break
                        except json.decoder.JSONDecodeError:
                            if_send = 1
                        except Exception as e:
                            self.err_str.append(str(e))
                            self.logging.error(str(__name__) + ".SendFailedLog.send_mail\n:" + str(e))
                            if_send = 0

                        try:
                            if if_send:
                                owner_obj = PyScriptOwnerListV2.objects.get(programs__sid=int(sid))
                                mail = owner_obj.mail
                                program_obj = PyScriptBaseInfoV2.objects.get(sid=int(sid))
                                name = program_obj.name
                                path = program_obj.path.path
                                name = '{0}{1}'.format(path, name)
                                owner = owner_obj.owner
                                message = '''
sid:{sid}
责任人:{owner}
服务器信息:{server_info}
说明：
  1.阿里云环境需要将域名更换为192.168.2.150进行接口调用
  2.内网环境直接使用域名调用
程序执行状态：{state}
产生时间：{occur_datetime}
程序日志信息：
{info}
                                            '''.format(owner=owner, state=state, occur_datetime=occur_datetime,
                                                       info=msg, sid=sid, server_info=server_info)
                                title = '程序执行信息 - 接口：{name}'.format(name=name)

                                send_mail(title, message, settings.DEFAULT_FROM_EMAIL, [admin_mail, mail],)
                                self.logging.info("send mail - program info: sid:{sid},hash_id:{hash_id}".
                                                  format(msg=msg, sid=sid, hash_id=hash_id))
                        except Exception as e:
                            self.err_str.append(str(e))
                            self.logging.error(__name__ + ":{err}".format(err=str(e)))
                            return
            if 'tid' in log:
                if 'type' in log and log['type'] == 102:
                    tid = log['tid']
                    hash_id = log['hash_id']
                    msg_type = int(log['type'])
                    event_odj = EventsHub.objects.get(hash_id=hash_id)
                    msg = event_odj.info
                    send_mail('质控错误', msg, settings.EMAIL_FROM, [admin_mail])
        except Exception as e:
            print(e)
            err_str = str(e)
            self.err_str.append(err_str)
        finally:
            sleep(0.1)
            ch.basic_ack(delivery_tag=method.delivery_tag)


def is_connection_usable():
    try:
        connection.connection.ping()
    except Exception as e:
        return False
    else:
        return True


if __name__ == "__main__":
    pass
    # body_r = {"sid": 378, "hash_id": "85f07d9406dea45e", "subversion":
    # "2018-04-25 07:00:00", "type": 2, "occur_datetime": "2018-04-25 07:00:58"}
    # a = SendFailedLog()
    # a.send_mail(json.dumps(body_r).encode('utf-8'))
