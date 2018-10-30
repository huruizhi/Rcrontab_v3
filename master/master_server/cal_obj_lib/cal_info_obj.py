from master_server.mongo_models import CalProgramInfo


class CalInfoObj:
    def __init__(self, sid, pre_tables, result_tables, api, hash_ack):
        self.sid = sid
        self.info_dict = self.get_info_from_mongodb()
        info_dict_new = {'sid': sid, 'result_tables': result_tables, 'pre_tables': pre_tables,
                         'api': api, 'hash_ack': hash_ack}

        # mongodb中不存在项目信息，说明是新项目
        if not self.info_dict:
            # 创建空指针
            info_dict_new['pointer'] = ''
            self.info_dict = info_dict_new
            self.write_info_to_mongodb()

        # 项目信息更改
        elif self.info_dict['hash_ack'] != hash_ack:
            self.update_info_to_mongodb(**info_dict_new)
            self.info_dict = self.get_info_from_mongodb()

        # Info指针
        self.pointer = self.info_dict['pointer']

    # 数据改变
    def info_change(self,  sid, pre_tables, result_tables, api, hash_ack):
        info_dict_new = {'sid': sid, 'result_tables': result_tables, 'pre_tables': pre_tables,
                         'api': api, 'hash_ack': hash_ack}
        self.update_info_to_mongodb(**info_dict_new)
        self.info_dict = self.get_info_from_mongodb()

    # 部署服务器更改
    def server_change(self, server_id):
        self.update_info_to_mongodb(**{'server_id': server_id})

    # 修改指针
    def change_pointer(self, pointer):
        try:
            self.pointer = pointer
            self.info_dict['pointer'] = self.pointer
            info_obj = CalProgramInfo.objects(sid=self.sid)
            print(self.info_dict['pointer'])
            info_obj.update(**self.info_dict)
        except Exception as e:
            print(e)

    # 将info写入mongodb
    def write_info_to_mongodb(self):
        cal_program = CalProgramInfo(**self.info_dict)
        cal_program.save()

    # 从mongodb读出数据
    def get_info_from_mongodb(self):
        info = dict()
        try:
            info_obj = CalProgramInfo.objects.get(sid=self.sid)
            # 转换成字典
            info = dict(info_obj.to_mongo())
            # 去掉Objectid
            info.pop('_id')
        except Exception as e:
            info = dict()
        finally:
            return info

    # 向mongodb更新信息
    def update_info_to_mongodb(self, **kwargs):
        info_obj = CalProgramInfo.objects(sid=self.sid)
        info_obj.update(**kwargs)
        self.info_dict = self.get_info_from_mongodb()




