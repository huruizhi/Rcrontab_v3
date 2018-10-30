import pymysql
from urllib import request, parse
from master_server.packages.log_module import quality_control


class QualityControl:
    def __init__(self, table_name):

        self.db = pymysql.connect("192.168.0.153", "py_qc", "5RDQ8Zel", "py_qc")

        # 使用 cursor() 方法创建一个游标对象 cursor
        self.cursor = self.db.cursor()
        self.sql_str = 'select  from regist_center where table_name like "%{table_name}%"'.format(table_name=table_name)

    def _exec_sql(self):
        num = self.cursor.execute(self.sql_str)
        if num:
            data = self.cursor.fetchone()
            qc_api = data[2]
            self.cursor.close()
            return qc_api
        else:
            self.cursor.close()
            return False

    def qc(self):
        api = self._exec_sql()
        if api:
            try:
                page = request.urlopen(api).read()
                page = page.decode('utf-8')
                quality_control.info(api)
                quality_control.info(page)
            except Exception as e:
                quality_control.error(api)
                quality_control.error(str(e))
            return True
        else:
            return False

    def ac(self):
        data_dict = {'table_name': 'pyStockMarketingInfo', 'hash_id': 'asdfsaawadsad', "extra_info": {}}
        url = 'http://192.168.0.156:4850/pyControl/controlAction/startControl'

        data = bytes(parse.urlencode(data_dict), encoding="utf8")

        req = request.Request(url=url, data=data, method="POST")

        response = request.urlopen(req)

        print(response.read().decode("utf-8"))
