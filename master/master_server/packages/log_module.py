import logging
import os

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


class WriteLogManage:
    def __init__(self, name):
        file_name = BASE_DIR + "/log/" + name + '_log.txt'
        logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        self.logger = logging.getLogger(name)
        handler = logging.FileHandler(file_name)
        formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        handler.setFormatter(formatter)
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
    if name == 'tables_listener':
        return tables_listener


write_log = WriteLogManage('events_listener')
send_mail = WriteLogManage('send_mail')
tables_listener = WriteLogManage('tables_listener')
result_reader = WriteLogManage('result_reader')
cal_log = WriteLogManage('cal_log')
mysql_sync = WriteLogManage('mysql_sync_api')
mysql_sync_result_reader = WriteLogManage('mysql_sync_result_reader')
scheduler_log = WriteLogManage('scheduler_log')
quality_control = WriteLogManage('quality_control')
mq_err = WriteLogManage('mq_err')


