from django.conf import settings
from django.core.mail import send_mail
from master_server.packages.receive import ReceiveRabbitMQMessage
from master_server.models import PyScriptOwnerListV2, PyScriptBaseInfoV2
from master_server.mongo_models import EventsHub
import json
from master_server.packages.log_module import WriteLog


# 发送邮件
class SendFailedLog:

    def start(self):
        mq = ReceiveRabbitMQMessage(name='send_mail', target=self.send_mail)
        mq.start()

    @staticmethod
    def send_mail(ch, method, properties, body):
        admin_mail = PyScriptOwnerListV2.objects.get(owner='admin').mail

        logging = WriteLog('send_mail')

        log = json.loads(body.decode('utf-8'))
        if 'sid' in log:
            sid = log['sid']
            hash_id = log['hash_id']
            msg_type = int(log['type'])
            occur_datetime = log['occur_datetime']
            try:
                event_odj = EventsHub.objects.get(hash_id=hash_id)
            except Exception as e:
                logging.warning("Cannot find hash_id: sid:{sid}, msg_type:{msg_type},hash_id:{hash_id}".
                                format(msg_type=msg_type, sid=sid, hash_id=hash_id))
                return
            msg = event_odj.info
            if msg_type in [3, 4, 5]:
                state = '失败'
                owner_obj = PyScriptOwnerListV2.objects.get(programs__sid=int(sid))
                mail = owner_obj.mail
                name = PyScriptBaseInfoV2.objects.get(sid=int(sid)).name
                owner = owner_obj.owner
                message = '''
                责任人:{owner}
                程序执行状态：{state}
                产生时间：{occur_datetime}
                程序日志信息：
                {info}
                '''.format(owner=owner, state=state, occur_datetime=occur_datetime, info=msg)

                title = '程序执行信息 - 接口：{name}'.format(name=name)

                send_mail(title, message, settings.DEFAULT_FROM_EMAIL, [mail, admin_mail],)
                logging.info("send mail - program info: sid:{sid},hash_id:{hash_id}".
                             format(msg=msg, sid=sid, hash_id=hash_id))

            if msg_type == 2:
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
                        print(str(__name__) + ".SendFailedLog.send_mail\n:" + str(e))
                        if_send = 0

                    if if_send:
                        owner_obj = PyScriptOwnerListV2.objects.get(programs__sid=int(sid))
                        mail = owner_obj.mail
                        name = PyScriptBaseInfoV2.objects.get(sid=int(sid)).name
                        owner = owner_obj.owner
                        message = '''
                                    责任人:{owner}
                                    程序执行状态：{state}
                                    产生时间：{occur_datetime}
                                    程序日志信息：
                                    {info}
                                    '''.format(owner=owner, state=state, occur_datetime=occur_datetime, info=msg)
                        title = '程序执行信息 - 接口：{name}'.format(name=name)

                        send_mail(title, message, settings.DEFAULT_FROM_EMAIL, [admin_mail, mail],)
                        logging.info("send mail - program info: sid:{sid},hash_id:{hash_id}".
                                     format(msg=msg, sid=sid, hash_id=hash_id))

        if log['type'] == 102:
            tid = log['tid']
            hash_id = log['hash_id']
            msg_type = int(log['type'])

            try:
                event_odj = EventsHub.objects.get(hash_id=hash_id)
                msg = event_odj.info
                send_mail('质控错误', msg, settings.EMAIL_FROM, [admin_mail])
            except Exception as e:
                logging.warning("Cannot find hash_id: tid:{tid}, msg_type:{msg_type},hash_id:{hash_id}".
                                format(msg_type=msg_type, tid=tid, hash_id=hash_id))


