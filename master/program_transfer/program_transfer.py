import os
import django
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "master.settings")
django.setup()
from master_server import models as m


class Trance:
    def __init__(self, from_db, des_db, source_server, des_server, des_net):
        self.from_db = from_db
        self.des_db = des_db
        self.source_server = source_server
        self.des_server = des_server
        self.d_ip, self.d_port = des_net

    def _trance_tables(self):
        tables = m.TablesInfo.objects.filter(db_server=self.from_db)
        for t in tables:
            new_table_dic = t.__dict__
            new_table_dic.pop('_state')
            new_table_dic.pop('id')
            new_table_dic['db_server'] = self.des_db
            print(new_table_dic)
            m.TablesInfo.objects.create(**new_table_dic)

    def _create_new_path(self, new_server_id):
        path = m.Path.objects.filter(server__name=self.source_server)
        for p in path:
            new_path = p.__dict__
            new_path.pop('_state')
            old_path_id = new_path.pop('id')
            new_path['project'] = new_path['project'].replace('_nf', '_pro')
            new_path['server_id'] = new_server_id
            print(new_path)
            try:
                path = m.Path.objects.get(server_id=new_server_id, path=new_path['path'])
            except Exception as e:
                path = m.Path.objects.create(**new_path)
            new_path_id = path.pk
            self._trance_api(old_path_id, new_path_id)

    def _trance_api(self, old_path, new_path_id):
        old_api = m.PyScriptBaseInfoV2.objects.filter(path__pk=old_path)
        for program in old_api:
            old_api_pk = program.pk
            api_info = program.__dict__
            api_info.pop('_state')
            api_info.pop('sid')
            api_info['path_id'] = new_path_id
            try:
                api = m.PyScriptBaseInfoV2.objects.get(path_id=new_path_id, name=api_info['name'])
            except Exception as e:
                api = m.PyScriptBaseInfoV2.objects.create(**api_info)
            self._change_pre_table(old_api_pk, api.pk)
            self._change_res_table(old_api_pk, api.pk)

    def _change_pre_table(self, old_api_pk, new_api_pk):
        print(old_api_pk, new_api_pk)
        old_api = m.PyScriptBaseInfoV2.objects.get(pk=old_api_pk)
        new_api = m.PyScriptBaseInfoV2.objects.get(pk=new_api_pk)
        if old_api.program_type == 1:
            old_pre_tables = m.TablesInfo.objects.filter(son_program__sid=old_api_pk)
            new_pre_tables = m.TablesInfo.objects.filter(son_program__sid=new_api_pk)
            for t in old_pre_tables:
                n_t = m.TablesInfo.objects.get(db_server=self.des_db, table_name=t.table_name, db_name=t.db_name)
                is_add = 1
                for i in new_pre_tables:
                    if i == n_t:
                        is_add = 0
                        break
                if is_add == 1:
                    print(n_t.__dict__)
                    new_api.pre_tables.add(n_t)

    def _change_res_table(self, old_api_pk, new_api_pk):
        print(old_api_pk, new_api_pk)
        new_api = m.PyScriptBaseInfoV2.objects.get(pk=new_api_pk)
        old_father_tables = m.TablesInfo.objects.filter(father_program__sid=old_api_pk)
        new_father_tables = m.TablesInfo.objects.filter(father_program__sid=new_api_pk)
        print(new_father_tables)
        for t in old_father_tables:
            n_t = m.TablesInfo.objects.get(db_server=self.des_db, table_name=t.table_name, db_name=t.db_name)
            is_add = 1
            for i in new_father_tables:
                if i == n_t:
                    is_add = 0
                    break
            if is_add == 1:
                print(n_t)
                new_api.result_tables.add(n_t)

    def _create_new_server(self):
        server = m.ServerInfo.objects.get(name=self.source_server)
        new_server_info = server.__dict__
        new_server_info.pop('_state')
        new_server_info.pop('id')
        print(new_server_info)
        new_server_info['ip'] = self.d_ip
        new_server_info['port'] = self.d_port
        new_server_info['name'] = self.des_server
        print(new_server_info)
        try:
            s = m.ServerInfo.objects.get(ip=self.d_ip, port=self.d_port)
        except Exception as e:
            s = m.ServerInfo.objects.create(**new_server_info)
        return s.pk

    def start(self):
        self._trance_tables()
        server_id = self._create_new_server()
        print(server_id)
        self._create_new_path(server_id)


if __name__ == '__main__':
    s_db = 'db_fof_v3_pro'  # 源数据库标识
    s_server = '阿里-fof_v3_测试'  # 服务器标志
    d_db = 'db_fof_v3_pro_ali'  # 目的数据库标识
    d_server = '阿里-fof_v3_正式'
    d_network = ('172.16.74.19', 7061)

    trance = Trance(s_db, d_db, s_server, d_server, d_network)
    trance.start()



