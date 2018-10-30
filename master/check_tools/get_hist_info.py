import master_server.mongo_models as mo
import master_server.models as mm


class GetHistInfo:
    def __init__(self, sid, pre=None):
        self.sid = sid
        program = mm.PyScriptBaseInfoV2.objects.get(sid=sid)
        self.hist_info = None
        if program.program_type == 0:
            self.hist_info = _GetCronExecHistInfo(sid, pre)
        elif program.program_type == 1:
            self.hist_info = _GetCalExecHistInfo(sid, pre)

    def __call__(self, *args, **kwargs):
        if self.hist_info:
            return self.hist_info()
        else:
            return {'error': 'sid {sid} is not exist!'.format(sid=self.sid)}


class _GetCalExecHistInfo:
    """
    查询计算程序执行的历史情况
    """
    def __init__(self, sid, pre=None):
        """
        :param sid: 查询的程序sid
        :param pre: 需要查询的历史版本数量默认为5
        """
        self.sid = sid
        self.pre = pre if pre else 5

    def __call__(self, *args, **kwargs):
        cal_tree_list = list()
        c_i = mo.CalProgramInfo.objects.get(sid=self.sid)
        pointer = c_i.pointer
        c_t = mo.CalVersionTree.objects.get(hash_id=pointer)
        for i in range(self.pre):
            cal_tree_dict = self._get_tree(c_t)
            cal_tree_list.append(cal_tree_dict)

            # 判断前置表是否存在
            hash_id = c_t.hash_id
            c_t = self._get_pre_tree_exist(hash_id)
            if not c_t:
                break
        return cal_tree_list

    def _get_tree(self, c_t):
        """

        :param c_t: 计算程序cal_tree 对象
        :return: 计算程序执行 信息
        """
        cal_tree_dict = dict()
        if hasattr(c_t, 'sid'):
            cal_tree_dict['sid'] = c_t.sid
        if hasattr(c_t, 'status'):
            cal_tree_dict['status'] = c_t.status
        if hasattr(c_t, 'running_start'):
            if c_t.running_start is not None:
                cal_tree_dict['running_start'] = self._get_start_time(c_t.running_start)
        if hasattr(c_t, 'running_end'):
            if c_t.running_end is not None:
                cal_tree_dict['running_end'] = self._get_end_time(c_t.running_end)
        if hasattr(c_t, 'pre_tables'):
            pre_tables = c_t.pre_tables
            pre_tables = self._get_pre_tables(pre_tables)
            cal_tree_dict['pre_tables'] = pre_tables
        return cal_tree_dict

    @staticmethod
    def _get_pre_tree_exist(hash_id):
        c_t = mo.CalVersionTree.objects.get(hash_id=hash_id)
        hash_id = c_t.pre_version
        if hash_id == 'init':
            return False
        c_t = mo.CalVersionTree.objects.get(hash_id=hash_id)
        return c_t

    @staticmethod
    def _get_start_time(hash_id):
        event_info = dict()
        event = mo.EventsHub.objects.get(hash_id=hash_id)
        try:
            event_info['version'] = event.version.strftime('%Y-%m-%d')
            event_info['subversion'] = event.subversion.strftime('%Y-%m-%d %H-%M-%S')
            event_info['occur_datetime'] = event.occur_datetime.strftime('%Y-%m-%d %H-%M-%S')
            event_info['status'] = event.status
        except Exception as e :
            event_info['status'] = event.status
        finally:
            return event_info

    @staticmethod
    def _get_end_time(hash_id):
        event_info = dict()
        event = mo.EventsHub.objects.get(hash_id=hash_id)
        try:
            event_info['version'] = event.version.strftime('%Y-%m-%d')
            event_info['subversion'] = event.subversion.strftime('%Y-%m-%d %H-%M-%S')
            event_info['occur_datetime'] = event.occur_datetime.strftime('%Y-%m-%d %H-%M-%S')
            event_info['info'] = event.info
            event_info['type'] = event.status
        except Exception as e:
            event_info['type'] = event.status
        finally:
            return event_info

    @staticmethod
    def _get_pre_tables(pre_tables):
        tables_info = dict()
        for table_id, hash_id in pre_tables.items():
            table_info = dict()
            try:
                table_info['status'] = 'flushed'
                event = mo.EventsHub.objects.filter(hash_id=hash_id)[0]
                table_info['version'] = event.version
                table_info['occur_datetime'] = event.occur_datetime.strftime('%Y-%m-%d %H-%M-%S')
                if hasattr(event, 'source'):
                    table_info['source'] = event.source
            except Exception as e:
                tables_info[table_id] = {'status': pre_tables[table_id]}
        return tables_info


class _GetCronExecHistInfo:
    """
    查询计算程序执行的历史情况
    """
    def __init__(self, sid, pre=None):
        """
        :param sid: 查询的程序sid
        :param pre: 需要查询的历史版本数量默认为5
        """
        self.sid = sid
        self.pre = pre if pre else 5

    def __call__(self, *args, **kwargs):
        cron_tree_list = list()
        c_i = mo.CronProgramInfo.objects.get(sid=self.sid)
        pointer = c_i.pointer
        c_t = mo.CronProgramVersionTree.objects.get(hash_id=pointer)
        for i in range(self.pre):
            cron_tree_dict = self._get_tree(c_t)
            cron_tree_list.append(cron_tree_dict)

            # 判断前置表是否存在
            hash_id = c_t.hash_id
            c_t = self._get_pre_tree_exist(hash_id)
            if not c_t:
                break
        return cron_tree_list

    def _get_tree(self, c_t):
        """

        :param c_t: 计算程序cal_tree 对象
        :return: 计算程序执行 信息
        """
        cron_tree_dict = dict()
        if hasattr(c_t, 'sid'):
            cron_tree_dict['sid'] = c_t.sid
        if hasattr(c_t, 'status'):
            cron_tree_dict['status'] = c_t.status
        if hasattr(c_t, 'running_start'):
            if c_t.running_start is not None:
                cron_tree_dict['running_start'] = self._get_start_time(c_t.running_start)
        if hasattr(c_t, 'running_end'):
            if c_t.running_end is not None:
                cron_tree_dict['running_end'] = self._get_end_time(c_t.running_end)
        return cron_tree_dict

    @staticmethod
    def _get_pre_tree_exist(hash_id):
        c_t = mo.CronProgramVersionTree.objects.get(hash_id=hash_id)
        hash_id = c_t.pre_version
        if hash_id == 'init':
            return False
        c_t = mo.CronProgramVersionTree.objects.get(hash_id=hash_id)
        return c_t

    @staticmethod
    def _get_start_time(hash_id):
        event_info = dict()
        event = mo.EventsHub.objects.get(hash_id=hash_id)
        try:
            event_info['version'] = event.version.strftime('%Y-%m-%d')
            event_info['subversion'] = event.subversion.strftime('%Y-%m-%d %H-%M-%S')
            event_info['occur_datetime'] = event.occur_datetime.strftime('%Y-%m-%d %H-%M-%S')
            event_info['status'] = event.status
        except Exception as e :
            event_info['status'] = event.status
        finally:
            return event_info

    @staticmethod
    def _get_end_time(hash_id):
        event_info = dict()
        event = mo.EventsHub.objects.get(hash_id=hash_id)
        try:
            event_info['version'] = event.version.strftime('%Y-%m-%d')
            event_info['subversion'] = event.subversion.strftime('%Y-%m-%d %H-%M-%S')
            event_info['occur_datetime'] = event.occur_datetime.strftime('%Y-%m-%d %H-%M-%S')
            event_info['info'] = event.info
            event_info['type'] = event.status
        except Exception as e:
            event_info['type'] = event.status
        finally:
            return event_info

