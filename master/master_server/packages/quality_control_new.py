import pymysql
import requests
import datetime


class QualityControl:
    def __init__(self):

        self.db = pymysql.connect("192.168.0.153", "py_qc", "5RDQ8Zel", "py_qc")
        self.today = datetime.datetime.now().strftime('%Y-%m-%d')
        self.today_chabu_fenhong = (datetime.datetime.now() - datetime.timedelta(days=5)).strftime('%Y-%m-%d')
        # 使用 cursor() 方法创建一个游标对象 cursor

    def _get_api(self):
        cursor = self.db.cursor()
        sql_str = 'select table_name,api from regist_center'
        cursor.execute(sql_str)
        api_info = cursor.fetchall()
        cursor.close()
        return api_info

    def _delay_qc(self, table_name):
        cursor = self.db.cursor()
        sql_str = 'select days from delay_qc where table_name = "{table_name}"'.format(table_name=table_name)
        num = cursor.execute(sql_str)
        if num:
            return cursor.fetchone()
        else:
            return False

    def _py_etl_fund_pro_dividend_2_1(self):
        cursor = self.db.cursor()
        sql_str = '''
INSERT IGNORE into py_etl_qc.py_etl_fund_pro_dividend_2_1 
select fund_code,ex_dividend_date,paydate_dividend,record_date,dividendper_share,NULL as qc_source,NULL as  type,2 as is_check 
from py_etl.py_etl_fund_pro_dividend_2_1 
where 
ex_dividend_date > '{today}'
        '''.format(today=self.today_chabu_fenhong)
        num = cursor.execute(sql_str)
        cursor.close()
        print(num)

    def _py_etl_fund_split_info_2_1(self):
        cursor = self.db.cursor()
        sql_str = '''
INSERT IGNORE into py_etl_qc.py_etl_fund_split_info_2_1
select fund_code, split_date, split_type, conversion_ratio,
 NULL as qc_source,NULL as  type,2 as is_check 
 from py_etl.py_etl_fund_split_info_2_1 
where split_date>'{today}'
                '''.format(today=self.today_chabu_fenhong)
        num = cursor.execute(sql_str)
        cursor.close()
        print(num)

    @staticmethod
    def _exec_qc(api, delay_days=None):
        try:
            if not delay_days:
                r = requests.get(api)
                print(api)
                print(r)
                print('======')
            else:
                qc_date_obj = datetime.datetime.now() - datetime.timedelta(days=delay_days)
                qc_date = qc_date_obj.strftime('%Y-%m-%d')
                data = {'start_date': qc_date, 'end_date': qc_date, 'ids': None}
                r = requests.post(api, data=data)
                print(api)
                print(r)
                print('======')
        except Exception as e:
            print(api)
            print(str(e))

    def __call__(self, *args, **kwargs):
        api_info = self._get_api()
        for table_name, api in api_info:
            print(table_name, api)
            is_delay = self._delay_qc(table_name)
            self._exec_qc(api, is_delay)
        self._py_etl_fund_pro_dividend_2_1()
        self._py_etl_fund_split_info_2_1()


if __name__ == '__main__':
    qc = QualityControl()
    qc()
