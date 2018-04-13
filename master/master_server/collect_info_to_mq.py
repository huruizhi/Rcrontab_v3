from master_server.mongo_models import EventsHub
import json
from master_server.packages.event_product import EventProduct

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
        try:
            data = json.dumps(self.msg)
            event_product = EventProduct()
            event_hub = EventsHub(**self.msg)
            event_hub.save()
            event_product.broadcast_message(data)
            event_product.close()
            return True
        except Exception as e:
            return False
