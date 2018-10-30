from django.test import TestCase

from master_server.models import PyScriptBaseInfoV2


def create_rerun_list(rerun_list, sid):
    programs_obj = PyScriptBaseInfoV2.objects.filter(pre_tables__father_program__sid=sid)
    programs = [{'pre_program': sid, 'sid': program.pk} for program in programs_obj]
    rerun_list += programs
    if not programs:
        for program in programs:
            create_rerun_list(rerun_list, program['sid'])

