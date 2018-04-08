from mongoengine import connect, Document
import mongoengine as mn
connect('EventsHub', host='192.168.0.156', port=27017)


events_type = {1: "running_start", 2: "running_end_success", 3: "running_end_info",
               4: "running_end_failed", 5: "running_end_timeout",
               101: "QC_success", 102: "QC_failed", 103: "QC_without"}

level_type = {3: "error", 2: "warning", 1: "info"}

status_dict = {1: "success", 0: "failed"}

lock_status = {1: "locked", 0: "unlock"}

data_source_dict = {1: "system2", 2: "program"}


class EventsHub(Document):
    hash_id = mn.StringField(max_length=16, required=True)
    sid = mn.IntField()
    tid = mn.IntField()
    type = mn.StringField(choices=events_type)
    info = mn.StringField(max_length=1000)
    version = mn.DateTimeField()
    occur_datetime = mn.DateTimeField()
    level = mn.StringField()


class CronProgramVersionTree(Document):
    hash_id = mn.StringField(max_length=16, required=True)
    sid = mn.IntField()
    running_start = mn.DateTimeField()
    running_end = mn.DateTimeField()
    status = mn.StringField(choices=status_dict)
    pre_version = mn.StringField(max_length=16, equired=True)
    begin_deadline = mn.DateTimeField()
    end_deadline = mn.DateTimeField()


class CronProgramInfo(Document):
    sid = mn.IntField()
    lock = mn.StringField(choices=lock_status)
    result_tables = mn.ListField()
    cron_program_version = mn.StringField(max_length=16)


class TableVersionTree(Document):
    hash_id = mn.StringField(max_length=16, required=True)
    tid = mn.IntField()
    new_p_version = mn.DictField()
    old_p_version = mn.DictField()
    pre_t_version = mn.StringField(max_length=16, required=True)
    QC = mn.StringField(max_length=16)


class TableInfo(Document):
    tid = mn.StringField()
    latest_version = mn.StringField(max_length=16, required=True)
    data_source = mn.StringField(choices=data_source_dict)


class CalculateVersionTree(Document):
    hash_id = mn.StringField(max_length=16, required=True)
    sid = mn.IntField()
    running_start = mn.StringField(max_length=16)
    running_end = mn.StringField(max_length=16)
    pre_t_new_version = mn.DictField()
    pre_t_old_version = mn.DictField()
    status = mn.StringField(choices=status_dict)
    pre_version = mn.StringField(max_length=16)
    end_deadline = mn.DateTimeField()


class CalProgramInfo(Document):
    sid = mn.IntField()
    lock = mn.StringField(choices=lock_status)
    pre_tables = mn.ListField()
    result_tables = mn.ListField()
    cal_program_version = mn.StringField(max_length=16)

