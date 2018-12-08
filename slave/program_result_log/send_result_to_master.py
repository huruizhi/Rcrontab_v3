from slave.settings import STATIC_VARIABLE
from slave_server.packages.log_module import result_reader
import requests
from time import sleep


class SendRstToMaster:
    def __init__(self, info):
        master_ip = STATIC_VARIABLE['MASTER_IP']
        master_port = STATIC_VARIABLE['MASTER_PORT']
        self.url = 'http://{ip}:{port}/master_server/slave_program_result/'.format(ip=master_ip, port=master_port)
        if isinstance(info, str):
            self.info = info
        else:
            raise Exception('传输对象必须为字符串')

    def send_msg(self):
        while True:
            result_reader.info(self.info)
            try:
                r = requests.post(self.url, data={'result': self.info})
                result_reader.info(r.text)
                return True
            except Exception as e:
                result_reader.info('{err}'.format(err=e))
                sleep(5)


