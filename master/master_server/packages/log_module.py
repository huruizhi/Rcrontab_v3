import logging
import os

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


class WriteLogManage:
    def __init__(self, name):
        file_name = BASE_DIR + '/log.txt'
        logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        self.logger = logging.getLogger(name)
        handler = logging.FileHandler(file_name)
        self.logger.addHandler(handler)

    def info(self, msg):
        self.logger.info(msg)

    def warning(self, msg):
        self.logger.warning(msg)

    def error(self, msg):
        self.logger.error(msg)


def WriteLog(name):
    if name == 'events_listener':
        return write_log
    if name == 'send_mail':
        return send_mail


write_log = WriteLogManage('events_listener')
send_mail = WriteLogManage('send_mail')
