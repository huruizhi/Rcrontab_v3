import pymysql
import datetime


class QualityControl:
    def __init__(self):

        self.db = pymysql.connect("192.168.0.153", "py_qc", "5RDQ8Zel", "py_qc")
        self.today = datetime.datetime.now().strftime('%Y-%m-%d')

        # 使用 cursor() 方法创建一个游标对象 cursor

    def _get_tables(self):
        cursor = self.db.cursor()
        sql_str = 'select table_name from qc_web_api_record'
        cursor.execute(sql_str)
        table_info = cursor.fetchall()
        tables_info = list()
        for table in table_info:
            tables_info.append(table[0])
        return tables_info

    def _get_all_qc_table(self):
        sql_str = """SELECT concat(`table_schema`,'.',`table_name`) as table_name
FROM INFORMATION_SCHEMA.`tables`
WHERE table_schema like '%_qc' and table_schema != 'py_qc'"""
        cursor = self.db.cursor()
        cursor.execute(sql_str)
        table_info = cursor.fetchall()
        tables_info = list()
        for table in table_info:
            tables_info.append(table[0])
        return tables_info

    def __call__(self, *args, **kwargs):
        tables = self._get_tables()
        qc_tables = self._get_all_qc_table()
        create_api = [table for table in qc_tables if table not in tables]
        return create_api


class CreateAPI:
    @staticmethod
    def get_sql():
        db = pymysql.connect(host='192.168.0.153', port=3306, user='huruizhi', passwd='hrz123', charset="utf8")
        cursor_1 = db.cursor()
        return cursor_1

    def get_info(self, db_name_org, table):
        db_name = db_name_org
        cursor_2 = self.get_sql()
        sql_key = """SELECT column_name
      FROM INFORMATION_SCHEMA.`KEY_COLUMN_USAGE`
      WHERE table_name='{table}'
      AND table_schema='{db}'
      AND constraint_name='PRIMARY'""".format(table=table, db=db_name)
        cursor_2.execute(sql_key)
        columns_keys = [i[0] for i in cursor_2.fetchall()]
        cursor_2.close()

        cursor_1 = self.get_sql()

        sql_col = "select COLUMN_NAME,column_comment from information_schema.COLUMNS where table_name='{table}' " \
                  "and table_schema = '{db}';".format(table=table, db=db_name)

        cursor_1.execute(sql_col)
        data = cursor_1.fetchall()
        columns = [(i[0], i[1]) for i in data if i[0] not in columns_keys]
        columns_key = [(i[0], i[1]) for i in data if i[0] in columns_keys]
        str = '''requestbody:
        {
        "table_name":"%s.%s",  //表名称
        "id":{   //主键''' % (db_name_org, table)
        print(str)

        for i in columns_key:
            print('         "{col}":"",//{com}'.format(col=i[0], com=i[1].replace('\n', '')))
        print('''      },
      "data":{   //更改的数据''')
        for i in columns:
            print('     "{col}":"",//{com}'.format(col=i[0], com=i[1].replace('\n', '')))
        print('''
            }
        }''')


if __name__ == '__main__':
    qc = QualityControl()
    create_api = qc()
    for table_name in create_api:
        db = table_name.split('.')[0]
        table_n = table_name.split('.')[1]
        ca = CreateAPI()
        ca.get_info(db, table_n)
