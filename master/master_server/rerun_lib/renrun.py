from master_server.models import PyScriptBaseInfoV2, TablesInfo
from master_server.mongo_models import ReRunLog
from datetime import datetime


class ReRun:
    def __init__(self, sid):
        self.entry = sid
        self.rerun_list = {str(self.entry): {'pre_program': [], 'status': 0}}
        self.create_rerun_list(self.entry)
        subversion = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        rerun_info = {'subversion': subversion, 'rerun_list': self.rerun_list, 'entry': self.entry}
        ReRunLog(**rerun_info).save()

    def create_rerun_list(self, pre_sid):
        programs_obj = PyScriptBaseInfoV2.objects.filter(pre_tables__father_program__sid=pre_sid)
        programs = [program.pk for program in programs_obj]
        for sid in programs:
            if sid in self.rerun_list:
                self.rerun_list[str(sid)]['pre_program'].append(pre_sid)
            else:
                self.rerun_list[str(sid)] = {'pre_program': {pre_sid: 0}, 'status': 0}
        if not programs:
            for program in programs:
                self.create_rerun_list(program['sid'])

