from master_server.models import PyScriptBaseInfoV2, TablesInfo


class MaintainProgram:

    def maintain(self):
        programs = PyScriptBaseInfoV2.objects.filter(program_type=0)
        programs_info = dict()
        for program in list(programs):
            result_tables = TablesInfo.objects.filter(father_program=program)
            result_tables_list = []
            for result_table in result_tables:
                result_tables_list.append(result_table.pk)

            server = program.
            program_info = {'sid': program.sid, 'result_tables': result_tables_list}
            programs_info['']
