from master_server.cron_obj_lib.maintain_programs import MaintainPrograms
from master_server.cal_obj_lib.maintain_programs import MaintainCalProgram
from master_server.mail_failed_log import SendFailedLog
from threading import Thread, Lock
import json


class ThreadManagement:
    _instance_lock = Lock()

    def __init__(self):
        self._threads = list()
        # self.send_log_obj = SendFailedLog()
        self.maintain_cron = MaintainPrograms()
        self.maintain_cal = MaintainCalProgram()
        # self.mysql_sync = MysqlSync()
        self.count = 0

    def __new__(cls, *args, **kwargs):
        if not hasattr(ThreadManagement, "_instance"):
            with ThreadManagement._instance_lock:
                if not hasattr(ThreadManagement, "_instance"):
                    ThreadManagement._instance = object.__new__(cls)
        return ThreadManagement._instance

    def begin(self):
        if self.count == 0:
            self.count = self.count + 1
            self._threads.append(Thread(target=self.maintain_cron.loop_check_table, name='Spider program info MG'))
            # self._threads.append(Thread(target=self.send_log_obj.start, name='SendMail'))
            # self._threads.append(Thread(target=MaintainTables().start, name='maintain table info '))
            self._threads.append(Thread(target=self.maintain_cal.loop_check_table, name='calculate program info MG'))
            # self._threads.append(Thread(target=self.mysql_sync.table_events_listener, name='call mysql sync API'))

            for thread in self._threads:
                thread.start()
            return True
        else:
            return False

    def check(self):
        alive_dict = dict()
        for thread in self._threads:
            alive_dict[str(thread.name)] = str(thread.is_alive())

        alive_dict = json.dumps(alive_dict)
        return alive_dict

    def check_mail(self):
        return self.send_log_obj.err_str


ThreadManage = ThreadManagement()
