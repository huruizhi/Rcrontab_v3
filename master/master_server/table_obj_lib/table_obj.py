from master_server.models import TablesInfo as MysqlTablesInfo
from master_server.mongo_models import TableInfo
from master_server.table_obj_lib.table_tree_obj import TableTreeInfo


class TableObj:
    def __init__(self, tid):
        self.tid = tid
        # 获取 对象数据
        self.table_info = self.get_info_from_mongodb()

        # 不存在则新建
        if not self.table_info:
            table_mysql_obj = MysqlTablesInfo.objects.get(pk=self.tid)
            db_server = table_mysql_obj.db_server
            db_name = table_mysql_obj.db_name
            table_name = table_mysql_obj.table_name

            self.table_tree_obj = TableTreeInfo(self.tid)
            pointer = self.table_tree_obj.hash_id
            self.table_info = {'tid': self.tid, 'db_server': db_server, 'db_name': db_name, 'table_name': table_name,
                               'pointer': pointer}
            table_obj = TableInfo(**self.table_info)
            table_obj.save()
        else:
            pointer = self.table_info['pointer']
            self.table_tree_obj = TableTreeInfo(tid=self.tid, hash_id=pointer)

    def update(self, sid, hash_id, version):

        # 调用 table_tree_obj
        self.table_tree_obj.update(sid=sid, hash_id=hash_id, version=version)

        # 质控成功
        if self.table_tree_obj.table_tree_info['QC_status'] in (101, 103):

            # 创建新的 tree  对象
            self.table_update_success()

    def get_info_from_mongodb(self):
        info = dict()
        try:
            info_obj = TableInfo.objects.get(tid=self.tid)
            # 转换成字典
            info = dict(info_obj.to_mongo())

            # 去掉Object_id
            info.pop('_id')
        except Exception as e:
            info = dict()
        finally:
            return info

    def table_update_success(self):
        hash_id = self.table_tree_obj.table_tree_info['hash_id']

        self.table_tree_obj = TableTreeInfo(tid=self.tid, pre_version=hash_id)

        # 修改指针
        self.table_info['pointer'] = self.table_tree_obj.table_tree_info['hash_id']
        # 更新 mongodb数据库
        table_obj = TableInfo.objects.filter(tid=self.tid)
        table_obj.update(**self.table_info)



