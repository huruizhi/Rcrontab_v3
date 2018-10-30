import master_server.models as mm


class ParenSonInfo:
    def __init__(self, sid):
        self.entry = sid

        self.father_list = dict()
        self.son_list = dict()
        self._create_father_list(self.entry)
        self._create_son_list(self.entry)

    def _create_father_list(self, son_sid):
        tables = mm.TablesInfo.objects.filter(son_program__pk=son_sid)
        programs_obj = set()
        for t in tables:
            # print(t.pk)
            try:
                t_name = t.table_name
                db_name = t.db_name
                table_153_obj = mm.TablesInfo.objects.filter(table_name=t_name).filter(db_name=db_name).filter(db_server='db_153')[0]
                t = table_153_obj
            except Exception as e:
                pass
            p_o = mm.PyScriptBaseInfoV2.objects.filter(result_tables=t)
            for p in p_o:
                programs_obj.add(p)

        for program in programs_obj:
            sid = program.pk
            name = program.name
            cron = program.cron
            owner = program.owner.pk
            func = program.function

            if str(sid) in self.father_list:
                if son_sid not in self.father_list[str(sid)]['son']:
                    self.father_list[str(sid)]['son'].append(son_sid)
            else:
                self.father_list[str(sid)] = {'sid': str(sid), 'info': (name, cron, owner, func), 'son': [son_sid, ]}
        if programs_obj:
            for program in programs_obj:
                if program.pk != son_sid:
                    self._create_father_list(program.pk)

    def _create_son_list(self, father_sid):
        tables = mm.TablesInfo.objects.filter(father_program__pk=father_sid)
        programs_obj = set()
        for t in tables:
            try:
                t_name = t.table_name
                db_name = t.db_name
                table_153_obj = mm.TablesInfo.objects.filter(table_name=t_name).filter(db_name=db_name).filter(db_server='db_153')[0]
                t = table_153_obj
            except Exception as e:
                pass
            p_o = mm.PyScriptBaseInfoV2.objects.filter(pre_tables=t)
            for p in p_o:
                programs_obj.add(p)

        for program in programs_obj:
            sid = program.pk
            name = program.name
            cron = program.cron
            owner = program.owner.pk
            func = program.function

            if str(sid) in self.son_list:
                if father_sid not in self.son_list[str(sid)]['father']:
                    self.son_list[str(sid)]['father'].append(father_sid)
            else:
                self.son_list[str(sid)] = {'sid': str(sid), 'info': (name, cron, owner, func), 'father': [father_sid, ]}
        if programs_obj:
            for program in programs_obj:
                if program.pk != father_sid:
                    self._create_son_list(program.pk)

    def __call__(self, *args, **kwargs):
        s_obj = mm.PyScriptBaseInfoV2.objects.get(pk=self.entry)
        s_obj_name = s_obj.name
        cron = s_obj.cron
        owner = s_obj.owner.pk
        func = s_obj.function
        parent_son_inf = dict()
        parent_son_inf['entry'] = {'sid': self.entry, 'info': (s_obj_name, cron, owner, func)}
        parent_son_inf['father_list'] = list()
        for _, i in self.father_list.items():
            parent_son_inf['father_list'].append(i)

        parent_son_inf['son_list'] = list()
        for _, i in self.son_list.items():
            parent_son_inf['son_list'].append(i)

        return parent_son_inf
