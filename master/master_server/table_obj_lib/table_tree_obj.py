from master_server.models import PyScriptBaseInfoV2
from master_server.packages.hash import get_hash
from master_server.mongo_models import TableVersionTree
from master_server import models as m
from datetime import datetime
from master_server.collect_info_to_mq import SendProgramStatus
from master_server.packages.quality_control import QualityControl

class TableTreeInfo:
    def __init__(self, tid, pre_version='init', hash_id=None):

        self.tid = tid
        self.version = ''
        if hash_id:
            self.hash_id = hash_id
            self.get_old_obj(hash_id)
        else:

            # 生成 father_program 字典
            script_objs = PyScriptBaseInfoV2.objects.filter(result_tables__pk=tid)
            program_version = dict()
            for script_obj in script_objs:
                program_version[str(script_obj.pk)] = ''

            # 成成 info 信息
            info = {'tid': tid, 'pre_version': pre_version, 'program_version': program_version, 'QC_status': 100}
            hash_id = get_hash(info)
            info['hash_id'] = hash_id
            self.hash_id = hash_id
            self.table_tree_info = info

            # 写入mongodb
            table_tree_info = TableVersionTree(**self.table_tree_info)
            table_tree_info.save()

    # 程序执行成功，
    def update(self, sid, hash_id, version):
        sid = str(sid)
        if sid in self.table_tree_info['program_version']:
            self.table_tree_info['program_version'][sid] = hash_id
        self._update_info()

        # 检查是否所有的father_program 都执行完成
        is_update = self._check_table_status()
        if is_update:
            qc_result = self._quality_control()
            if qc_result:
                # 质控成功
                self._qc_success(version)
            else:
                # 质控失败
                self._qc_failed(version)

    # 检查表是否update完成 需要所有额程序
    def _check_table_status(self):
        is_update = 1
        for _, hash_id in self.table_tree_info['program_version'].items():
            if not hash_id:
                is_update = 0
                break
        return is_update

    # 更新 mongodb
    def _update_info(self):
        tree_obj = TableVersionTree.objects(hash_id=self.table_tree_info['hash_id'])
        tree_obj.update(**self.table_tree_info)

    # 进行质控
    def _quality_control(self):
        try:
            table_name = m.TablesInfo.objects.get(tid=self.tid).table_name
            # qc = QualityControl(table_name)
            # qc.qc()
        finally:
            return True

    def _qc_success(self, version):
        occur_datetime = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        event_info = {'tid': self.tid, 'type': 101,
                      'info': 'table QC_success',
                      'occur_datetime': occur_datetime,
                      'version': version,
                      'source': "table tree hash:{hash_id}".format(hash_id=self.table_tree_info['hash_id'])}
        hash_id = get_hash(event_info)
        event_info['hash_id'] = hash_id

        SendProgramStatus(message=event_info, msg_type='t').send_msg()

        self.table_tree_info['QC_status'] = 101
        self.table_tree_info['QC_success'] = hash_id
        self.table_tree_info['version'] = version
        self._update_info()

    def _qc_failed(self, version):
        occur_datetime = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        event_info = {'tid': self.tid, 'type': 102,
                      'info': 'table QC_failed',
                      'occur_datetime': occur_datetime,
                      'version': version,
                      'source': "table tree hash:{hash_id}".format(hash_id=self.table_tree_info['hash_id'])}
        hash_id = get_hash(event_info)
        event_info['hash_id'] = hash_id

        SendProgramStatus(message=event_info, msg_type='t').send_msg()

        self.table_tree_info['QC_status'] = 102
        self.table_tree_info['QC_success'] = hash_id
        self.table_tree_info['version'] = version
        self._update_info()

    # 获取存在的对象
    def get_old_obj(self, hash_id):
        info = dict()
        try:
            info_obj = TableVersionTree.objects.get(hash_id=hash_id)
            # 转换成字典
            info = dict(info_obj.to_mongo())
            # 去掉Objectid
            info.pop('_id')
        except Exception as e:
            print(e)
        finally:
            self.table_tree_info = info


