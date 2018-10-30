from mysql_sync_log.loop_check_mysql_sync import LoopCheckMysqlSyncLog
from program_result_log.loop_check_program_result_log import LoopReadResultLog
from threading import Thread, Lock
import json
from slave.settings import IS_REMOTE


class ThreadManagement:
    _instance_lock = Lock()

    def __init__(self):
        self._threads = list()
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
            loop_read_result_log = LoopReadResultLog()
            if IS_REMOTE == 1:
                loop_check_mysql_sync = LoopCheckMysqlSyncLog()
                self._threads.append(Thread(target=loop_check_mysql_sync.loop_read_log,
                                            name='loop_check_mysql_sync'))
            self._threads.append(Thread(target=loop_read_result_log.loop_read_log, name='loop_read_program_result_log'))

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


ThreadManage = ThreadManagement()
