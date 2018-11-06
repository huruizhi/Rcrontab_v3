from master_server.mongo_models import EventsHub
import json
from master_server.packages.event_product import EventProduct, TableEventProduct
from master_server.packages.log_module import mq_err
import traceback
from time import sleep

"""
将程序 和表 的的状态信息 写入rabbitMQ 和 mongodb EventHub
"""


class SendProgramStatus:
    def __init__(self, message, msg_type):
        if msg_type not in ['t', 'p']:
            self.msg_type = False
        else:
            self.msg_type = msg_type
        self.msg = message

    def send_msg(self):
        if not self.msg_type:
            return
        data = json.dumps(self.msg)
        for i in range(10):
            try:
                if self.msg_type == 'p':
                    event_product = EventProduct()
                else:
                    event_product = TableEventProduct()
                event_hub = EventsHub(**self.msg)
                event_hub.save()
                event_product.broadcast_message(data)
                event_product.close()
                return True
            except Exception:
                sleep(10)
                mq_err.error("{message}\n{err}".format(message=data, err=traceback.format_exc()))


if __name__ == '__main__':
    info_dict = {'tid': 48, 'type': 101, 'info': 'QC_success', 'occur_datetime': '2018-04-20 11:13:10',
                 'source': "table tree hash_id:{hash_id}".format(hash_id=244)}

    # 发送成功信号
    # SendProgramStatus(message=info_dict, msg_type='t').send_msg()
