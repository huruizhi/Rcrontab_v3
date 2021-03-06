from mongoengine import connect, Document
import mongoengine as mn
connect('Rcrontab_v3', host='192.168.0.156', port=27017)


events_type = {1: "running_start", 2: "running_end_success", 3: "running_end_info",
               4: "running_miss_start", 5: "running_end_timeout",
               101: "QC_success", 102: "QC_failed", 103: "QC_without"}

level_type = {3: "error", 2: "warning", 1: "info"}

status_dict = {0: "waiting_start", 1: "running_start", 2: "running_end_success", 3: "running_end_info",
               4: "running_miss_start", 5: "running_end_timeout"}

lock_status = {1: "locked", 0: "unlock"}

data_source_dict = {1: "system2", 2: "program"}

QC_status = {100: "QC_init", 101: "QC_success", 102: "QC_failed", 103: "QC_without"}


class EventsHub(Document):
    hash_id = mn.StringField(max_length=16, required=True, Unique=True)
    sid = mn.IntField()
    tid = mn.IntField()
    type = mn.IntField(choices=events_type)
    info = mn.StringField()
    version = mn.DateTimeField()
    subversion = mn.DateTimeField()
    occur_datetime = mn.DateTimeField()
    source = mn.StringField(max_length=50)


class CronProgramVersionTree(Document):
    hash_id = mn.StringField(max_length=16, required=True, Unique=True)
    sid = mn.IntField(required=True)
    running_start = mn.StringField(max_length=16)
    running_end = mn.StringField(max_length=16)
    status = mn.IntField(choices=status_dict, required=True, default=0)
    pre_version = mn.StringField(max_length=16, equired=True)
    next_run_time = mn.DateTimeField(required=True)
    end_deadline = mn.DateTimeField()
    subversion = mn.DateTimeField()
    version = mn.DateTimeField()


class CronProgramInfo(Document):
    sid = mn.IntField(Unique=True, required=True)
    lock = mn.IntField(choices=lock_status, default=0, required=True)
    result_tables = mn.ListField()
    pre_tables = mn.ListField()
    cron = mn.StringField(max_length=50)
    api = mn.StringField(max_length=300)
    hash_ack = mn.StringField(max_length=16, required=True)
    server_id = mn.IntField()
    pointer = mn.StringField(max_length=16, required=True)


class TableVersionTree(Document):
    hash_id = mn.StringField(max_length=16, required=True, Unique=True)
    tid = mn.IntField()
    program_version = mn.DictField()
    pre_version = mn.StringField(max_length=16, required=True)
    QC_status = mn.IntField(required=True, choices=QC_status)
    QC_failed = mn.StringField(max_length=16)
    QC_success = mn.StringField(max_length=16)
    version = mn.DateTimeField()


class TableInfo(Document):
    tid = mn.IntField(Unique=True, required=True)
    pointer = mn.StringField(max_length=16, required=True)
    data_source = mn.StringField(choices=data_source_dict)
    db_server = mn.StringField(max_length=20)
    db_name = mn.StringField(max_length=30)
    table_name = mn.StringField(max_length=100)


class CalVersionTree(Document):
    hash_id = mn.StringField(max_length=16, required=True, Unique=True)
    sid = mn.IntField()
    running_start = mn.StringField(max_length=16)
    running_end = mn.StringField(max_length=16)
    pre_tables = mn.DictField()
    status = mn.IntField(choices=status_dict,required=True, default=0)
    pre_version = mn.StringField(max_length=16)
    end_deadline = mn.DateTimeField()
    version = mn.DateTimeField()


class CalProgramInfo(Document):
    sid = mn.IntField(Unique=True, required=True)
    lock = mn.StringField(choices=lock_status)
    pre_tables = mn.ListField()
    result_tables = mn.ListField()
    api = mn.StringField(max_length=300)
    hash_ack = mn.StringField(max_length=16, required=True)
    pointer = mn.StringField(max_length=16)


class ReRunLog(Document):
    subversion = mn.DateTimeField(required=True)
    rerun_list = mn.DictField()
    entry = mn.IntField()
