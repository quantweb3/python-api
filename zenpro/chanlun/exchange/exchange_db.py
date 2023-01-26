import contextlib
import pymysql
from dbutils.pooled_db import PooledDB

from chanlun import config
from chanlun.exchange.exchange import *

if config.DB_HOST != '':
    g_pool_db = PooledDB(pymysql,
                         mincached=5, maxcached=10, maxshared=10, maxconnections=20, blocking=True,
                         host=config.DB_HOST,
                         port=config.DB_PORT,
                         user=config.DB_USER,
                         passwd=config.DB_PWD,
                         db=config.DB_DATABASE, charset='utf8')
else:
    g_pool_db = None


class ExchangeDB(Exchange):
    """
    数据库行情
    """

    def __init__(self, market):
        """
        :param market: 市场 a A股市场 hk 香港市场 us 美股市场 currency 数字货币市场  futures 期货市场
        """
        self.market = market
        self.exchange = None
        self.online_ex = None

    def table(self, code):
        """
        根据 code  获取对应的数据表名称
        :param code:
        :return:
        """
        if self.market == 'hk':
            return 'stock_klines_' + code.replace('.', '_').lower()
        elif self.market == 'a':
            return 'a_stock_klines_' + code.replace('.', '_').lower()[:7]
        elif self.market == 'us':
            return 'us_klines'
        elif self.market == 'currency':
            return 'futures_klines_' + code.replace('/', '_').lower()
        elif self.market == 'futures':
            return 'futures_klines_' + code.replace('.', '_').replace('@', '_').lower()

    def create_tables(self, codes):
        """
        批量创建表
        :return:
        """
        global g_pool_db

        # 沪深 A 股的建表语句，增加 code，避免创建太多表
        code_sql = """
        create table %s (
                        code VARCHAR(12) not null,
                        dt DATETIME not null,
                        f VARCHAR(5) not null,
                        h decimal(20,8) not null,
                        l decimal(20, 8) not null,
                        o decimal(20, 8) not null,
                        c decimal(20, 8) not null,
                        v decimal(28, 8) not null,
                        UNIQUE INDEX dt_f (code, dt, f)
                    )
        """

        # 香港与数字货币，每个 code 创建一个表
        no_code_sql = """
        create table %s (
                        dt DATETIME not null,
                        f VARCHAR(5) not null,
                        h decimal(20,8) not null,
                        l decimal(20, 8) not null,
                        o decimal(20, 8) not null,
                        c decimal(20, 8) not null,
                        v decimal(28, 8) not null,
                        UNIQUE INDEX dt_f (dt, f)
                    )
        """

        db = g_pool_db.connection()
        cursor = db.cursor()
        for code in codes:
            table = self.table(code)
            with contextlib.suppress(Exception):
                # 删除并重新创建
                # cursor.execute(f'drop table {table}')
                create_sql = code_sql % table if self.market in ['a', 'us'] else no_code_sql % table

                cursor.execute(create_sql)
        cursor.close()
        db.close()

    def query_last_datetime(self, code, frequency) -> [None, str]:
        """
        查询交易对儿最后更新时间
        :param frequency:
        :param code:
        :return:
        """
        global g_pool_db

        db = g_pool_db.connection()
        cursor = db.cursor()
        table = self.table(code)
        if self.market in ['a', 'us']:
            cursor.execute("select dt from %s where code = '%s' and f = '%s' order by dt desc limit 1"
                           % (table, code, frequency))
        else:
            cursor.execute("select dt from %s where f = '%s' order by dt desc limit 1"
                           % (table, frequency))

        dt = cursor.fetchone()
        cursor.close()
        db.close()
        if dt is not None:
            if self.market == 'a':
                return dt[0].strftime('%Y-%m-%d')
            else:
                return dt[0].strftime('%Y-%m-%d %H:%M:%S')
        return None

    def insert_klines(self, code, frequency, klines):
        """
        批量添加交易对儿Kline数据
        :param code:
        :param frequency
        :param klines:
        :return:
        """
        global g_pool_db

        db = g_pool_db.connection()
        cursor = db.cursor()
        table = self.table(code)
        for kline in klines.iterrows():
            k = kline[1]
            if self.market in ['a', 'us']:
                sql = "replace into %s(code, dt, f, h, l, o, c, v) values ('%s', '%s', '%s', %f, %f, %f, %f, %f)" % (
                    table, code, k['date'].strftime('%Y-%m-%d %H:%M:%S'), frequency, k['high'], k['low'], k['open'],
                    k['close'],
                    k['volume'])
            else:
                sql = "replace into %s(dt, f, h, l, o, c, v) values ('%s', '%s', %f, %f, %f, %f, %f)" % (
                    table, k['date'].strftime('%Y-%m-%d %H:%M:%S'), frequency, k['high'], k['low'], k['open'],
                    k['close'],
                    k['volume'])
            cursor.execute(sql)
        db.commit()
        return

    def del_klines(self, code, frequency, _datetime):
        """
        删除一条记录
        """
        global g_pool_db

        db = g_pool_db.connection()
        cursor = db.cursor()
        table = self.table(code)
        if self.market in ['a', 'us']:
            sql = "delete from %s where code='%s' and f = '%s' and dt='%s'" % (
                table, code, frequency, _datetime.strftime('%Y-%m-%d %H:%M:%S'))
        else:
            sql = "delete from %s where f = '%s' and dt='%s'" % (
                table, frequency, _datetime.strftime('%Y-%m-%d %H:%M:%S'))
        cursor.execute(sql)
        db.commit()
        return

    def klines(self, code: str, frequency: str,
               start_date: str = None, end_date: str = None,
               args=None) -> [pd.DataFrame, None]:

        if args is None:
            args = {}
        global g_pool_db

        if start_date is not None and end_date is not None and 'limit' not in args:
            args['limit'] = None
        if 'limit' not in args:
            args['limit'] = 5000

        table = self.table(code)
        if self.market in ['a', 'us']:
            sql = "select dt, f, h, l, o, c, v from %s where code='%s' and f='%s'" % (table, code, frequency)
        else:
            sql = "select dt, f, h, l, o, c, v from %s where f='%s'" % (table, frequency)
        if start_date is not None:
            sql += " and dt >= '%s'" % start_date
        if end_date is not None:
            sql += " and dt <= '%s'" % end_date
        sql += ' order by dt desc'
        if args['limit'] is not None:
            sql += f" limit {args['limit']}"

        # print(sql)

        db = g_pool_db.connection()
        cursor = db.cursor()
        cursor.execute(sql)
        klines = cursor.fetchall()
        cursor.close()
        db.close()
        kline_pd = pd.DataFrame(klines, columns=['date', 'f', 'high', 'low', 'open', 'close', 'volume'])
        kline_pd = kline_pd.iloc[::-1]
        kline_pd['code'] = code
        kline_pd['date'] = pd.to_datetime(kline_pd['date'])  # .map(lambda d: d.to_pydatetime())
        kline_pd['open'] = kline_pd['open'].astype('float')
        kline_pd['close'] = kline_pd['close'].astype('float')
        kline_pd['high'] = kline_pd['high'].astype('float')
        kline_pd['low'] = kline_pd['low'].astype('float')
        kline_pd['volume'] = kline_pd['volume'].astype('float')

        kline_pd = kline_pd[['code', 'date', 'open', 'close', 'high', 'low', 'volume']]
        kline_pd = kline_pd.reset_index(drop=True)

        return kline_pd

    def convert_kline_frequency(self, klines: pd.DataFrame, to_f: str) -> pd.DataFrame:
        """
        转换K线周期
        TODO 美股的没有设置
        """
        if self.market == 'currency':
            return convert_currency_kline_frequency(klines, to_f)
        elif self.market == 'futures':
            return convert_futures_kline_frequency(klines, to_f)
        else:
            return convert_stock_kline_frequency(klines, to_f)

    def all_stocks(self):
        pass

    def now_trading(self):
        pass

    def ticks(self, codes: List[str]) -> Dict[str, Tick]:
        pass

    def stock_info(self, code: str) -> [Dict, None]:
        pass

    def stock_owner_plate(self, code: str):
        pass

    def plate_stocks(self, code: str):
        pass

    def balance(self):
        pass

    def positions(self, code: str = ''):
        pass

    def order(self, code: str, o_type: str, amount: float, args=None):
        pass
