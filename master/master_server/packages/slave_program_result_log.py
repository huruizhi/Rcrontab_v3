from master_server.mongo_models import EventsHub
from master_server.packages.hash import get_hash
import json
from master_server.packages.event_product import EventProduct
from master_server.packages.log_module import result_reader, mq_err
import traceback
from time import sleep



"""
循环检查数据库的log表
将log表的信息写入 RabbitMQ与 mongodb EventHub

"""


class SlaveResultLog:

    def __init__(self, event_info):
        self.event_info = json.loads(event_info)

    def input_msg(self):
        hash_id = get_hash(self.event_info)
        self.event_info['hash_id'] = hash_id
        event_info_message = self.event_info
        if 'source' in event_info_message:
            del event_info_message['source']
        message = json.dumps(event_info_message)
        for i in range(10):
            try:
                event_product = EventProduct()
                result_reader.info(message)
                event_product.broadcast_message(message=message)

                event_product.close()
                break
            except Exception:
                sleep(10)
                mq_err.error("{message}\n{err}".format(message=message, err=traceback.format_exc()))

        event = EventsHub(**self.event_info)
        event.save()
