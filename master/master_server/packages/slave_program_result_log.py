from master_server.models import ResultLog
from master_server.mongo_models import EventsHub
from datetime import datetime
from master_server.packages.hash import get_hash
import json
from master_server.packages.event_product import EventProduct
from time import sleep
from django.db.models import Max
from master_server.packages.log_module import result_reader
from master_server.packages.mysql_check import connection_usable


"""
循环检查数据库的log表
将log表的信息写入 RabbitMQ与 mongodb EventHub

"""


class SlaveResultLog:

    def __init__(self, event_info):
        self.event_info = json.loads(event_info)

    def input_msg(self):
        try:
            event_product = EventProduct()
            hash_id = get_hash(self.event_info)
            self.event_info['hash_id'] = hash_id
            event = EventsHub(**self.event_info)
            event.save()

            if 'source' in self.event_info:
                del self.event_info['source']

            event_info_message = self.event_info
            message = json.dumps(event_info_message)
            result_reader.info(message)
            event_product.broadcast_message(message=message)

            event_product.close()
        except Exception as e:
            print(str(__name__) + ".LoopReadResultLog._read_log:\n")
            print(e)
