"""
US Polygon 行情接口
"""

import datetime as dt

import polygon

import os, pytz
import pandas as pd
from chanlun import config
from chanlun import fun, rd
from chanlun.exchange.exchange import *

g_all_stocks = []


class ExchangePolygon(Exchange):
    """
    美股 Polygon 行情服务
    """

    def __init__(self):
        super().__init__()

        self.client = polygon.RESTClient(config.POLYGON_APIKEY)

        self.trade_days = None

    def all_stocks(self):
        """
        使用 Polygono 的方式获取所有股票代码
        美股获取所有标的时间比较长，直接从 json 文件中获取
        """
        global g_all_stocks
        if len(g_all_stocks) > 0:
            return g_all_stocks
        stocks = pd.read_csv(os.path.split(os.path.realpath(__file__))[0] + '/us_symbols.csv')
        for s in stocks.iterrows():
            g_all_stocks.append({'code': s[1]['code'], 'name': s[1]['name']})
        return g_all_stocks

        # 以下是从网络获取，免费版本要 3 分钟才可以
        # g_all_stocks = rd.get_ex('us_stocks_all')
        # if g_all_stocks is not None:
        #     return g_all_stocks
        # g_all_stocks = []
        # next_url = None
        # while True:
        #     try:
        #         tickers = self.client.reference_tickers_v3(next_url=next_url, limit=1000)
        #         for _t in tickers.results:
        #             g_all_stocks.append({'code': _t['ticker'], 'name': _t['name']})
        #         if len(tickers.results) < 1000:
        #             break
        #         next_url = tickers.next_url
        #         print(next_url)
        #         if next_url is None or len(next_url) == 0:
        #             break
        #     except Exception as e:
        #         # 免费的有每分钟请求数限制，超过就报错，等一分钟再试试
        #         print('polygon 免费版本有限速，等一分钟再试试')
        #         time.sleep(60)
        #
        # if len(g_all_stocks) > 0:
        #     rd.save_ex('us_stocks_all', 10 * 48 * 60 * 60, g_all_stocks)
        #
        # return g_all_stocks

    @staticmethod
    def format_kline_pg(symbol, sym_df):

        df = sym_df
        df.rename(columns={'Unnamed: 0': 'date'}, inplace=True)
        df.rename(
            columns={"time": "date", "dt": "date", "v": "volume", "h": "high", "c": "close", "o": "open",
                     "l": "low"}, inplace=True)
        # df.index.name = 'dt'
        # df['dt'] = df.index
        df.reset_index(level=0, inplace=True)

        df['code'] = symbol
        klines = df[['code', 'date', 'open', 'close', 'high', 'low', 'volume']]

        return klines

    def klines(self, code: str, frequency: str,
               start_date: str = None, end_date: str = None,
               args=None) -> [pd.DataFrame, None]:

        if args is None:
            args = {}
        frequency_map = {
            'y': 'year', 'q': 'quarter', 'm': 'month', 'w': 'week', 'd': 'day', '120m': 'hour', '60m': 'hour',
            '30m': 'minute', '15m': 'minute', '5m': 'minute', '1m': 'minute'
        }

        frequency_mult = {
            'y': 1, 'q': 1, 'm': 1, 'w': 1, 'd': 1, '120m': 2, '60m': 1, '30m': 30, '15m': 15, '5m': 5, '1m': 1
        }

        try:
            now_date = time.strftime('%Y-%m-%d')
            if end_date is None:
                _toDate = now_date
            else:
                _toDate = end_date
            if start_date is None:
                time_format = '%Y-%m-%d %H:%M:%S'
                if len(_toDate) == 10:
                    time_format = '%Y-%m-%d'
                end_datetime = dt.datetime(*time.strptime(_toDate, time_format)[:6])
                if frequency == '1m':
                    start_date = (end_datetime - dt.timedelta(days=15)).strftime(time_format)
                elif frequency == '5m':
                    start_date = (end_datetime - dt.timedelta(days=15)).strftime(time_format)
                elif frequency == '30m':
                    start_date = (end_datetime - dt.timedelta(days=75)).strftime(time_format)
                elif frequency == '60m':
                    start_date = (end_datetime - dt.timedelta(days=150)).strftime(time_format)
                elif frequency == '120m':
                    start_date = (end_datetime - dt.timedelta(days=150)).strftime(time_format)
                elif frequency == 'd':
                    start_date = (end_datetime - dt.timedelta(days=5000)).strftime(time_format)
                elif frequency == 'w':
                    start_date = (end_datetime - dt.timedelta(days=7800)).strftime(time_format)
                elif frequency == 'y':
                    start_date = (end_datetime - dt.timedelta(days=15000)).strftime(time_format)
            else:
                time_format = '%Y-%m-%d %H:%M:%S'
                if len(_toDate) == 10:
                    time_format = '%Y-%m-%d'
                start_date = pd.to_datetime(start_date).strftime(time_format) 

            resp = self.client.stocks_equities_aggregates(code.upper(), frequency_mult[frequency], frequency_map[frequency],
                                                          start_date, _toDate, limit=50000)
            df = pd.DataFrame(resp.results)
            df['dt'] = pd.to_datetime(df['t'], unit='ms')

            df = df.set_index('dt') 
            
            if frequency != 'd' and frequency != 'w' and frequency != 'm' and frequency != 'y':
                nyc = pytz.timezone('America/New_York')
                df.index = df.index.tz_localize(pytz.utc).tz_convert(nyc)
                df = df.between_time('09:30:00', '16:00:00') 
                
            df = df.reset_index()

            klines = self.format_kline_pg(code, df)

            if frequency in ['y', 'q', 'm', 'w']:
                klines['date'] = klines['date'].apply(self.__convert_date)

            klines = klines.sort_values('date')

            klines = klines[['code', 'date', 'open', 'close', 'high', 'low', 'volume']]

            return klines
        except Exception as e:
            print('polygon.io 获取行情异常 %s Exception ：%s' % (code, str(e)))

        return None

    def stock_info(self, code: str) -> [Dict, None]:
        """
        获取股票名称
        """
        resp = self.client.reference_tickers_v3(ticker=code.upper(), market="stocks", active=True)
        if resp.status == 'OK':
            stock = resp.results
            if len(stock) == 0:
                return None
            return {
                'code': stock[0]['ticker'],
                'name': stock[0]['name']
            }

    def ticks(self, codes: List[str]) -> Dict[str, Tick]:
        """
        使用富途的接口获取行情Tick数据
        """
        raise Exception('交易所不支持')

    def now_trading(self):
        """
        返回当前是否是交易时间
        """
        resp = self.client.reference_market_status
        if resp.market != 'closed':
            return True
        return False

    @staticmethod
    def __convert_date(dt):
        dt = fun.datetime_to_str(dt, '%Y-%m-%d')
        return fun.str_to_datetime(dt, '%Y-%m-%d')

    def stock_owner_plate(self, code: str):
        raise Exception('交易所不支持')

    def plate_stocks(self, code: str):
        raise Exception('交易所不支持')

    def balance(self):
        raise Exception('交易所不支持')

    def positions(self, code: str = ''):
        raise Exception('交易所不支持')

    def order(self, code: str, o_type: str, amount: float, args=None):
        raise Exception('交易所不支持')