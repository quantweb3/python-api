import os

import alpaca_trade_api as tradeapi
from alpaca_trade_api.rest import TimeFrame, TimeFrameUnit

import datetime as dt
from chanlun import config
from chanlun import fun
from chanlun.exchange.exchange import *

g_all_stocks = []


class ExchangeAlpaca(Exchange):

    def __init__(self):
        super().__init__()

        self.api = tradeapi.REST(
            key_id=config.ALPACA_APIKEY,
            secret_key=config.ALPACA_SECRET,
            api_version='v2'
        )

    def all_stocks(self):
        """
        获取所有股票代码
        """
        global g_all_stocks
        if len(g_all_stocks) > 0:
            return g_all_stocks
        stocks = pd.read_csv(os.path.split(os.path.realpath(__file__))[0] + '/us_symbols.csv')
        for s in stocks.iterrows():
            g_all_stocks.append({'code': s[1]['code'], 'name': s[1]['name']})
        return g_all_stocks

        # 以下是从网络获取
        # if len(g_all_stocks) > 0:
        #     return g_all_stocks
        # g_all_stocks = rd.get_ex('us_stocks_all')
        # if g_all_stocks is not None:
        #     return g_all_stocks
        # g_all_stocks = []
        #
        # g_all_stocks = [el.symbol for el in self.api.list_assets(status='active', asset_class='us_equity')]
        # if len(g_all_stocks) > 0:
        #     rd.save_ex('us_stocks_all', 24 * 60 * 60, g_all_stocks)
        #
        # return g_all_stocks

    @staticmethod
    def format_kline_pg(symbol, sym_df):
        df = sym_df
        df.rename(columns={'Unnamed: 0': 'date'}, inplace=True)
        df.rename(columns={
            "timestamp": "date",
            "dt": "date", "v": "volume",
            "h": "high", "c": "close", "o": "open", "l": "low"
        }, inplace=True)
        # df.index.name = 'dt'
        # df['dt'] = df.index
        df.reset_index(level=0, inplace=True)

        df['code'] = symbol
        return df[['code', 'date', 'open', 'close', 'high', 'low', 'volume']]

    def klines(self, code: str, frequency: str,
               start_date: str = None, end_date: str = None,
               args=None) -> [pd.DataFrame, None]:

        if args is None:
            args = {}
        frequency_map = {
            'y': TimeFrameUnit.Month, 'q': TimeFrameUnit.Month, 'm': TimeFrameUnit.Month, 'w': TimeFrameUnit.Week,
            'd': TimeFrameUnit.Day,
            '120m': TimeFrameUnit.Hour, '60m': TimeFrameUnit.Hour, '30m': TimeFrameUnit.Minute,
            '15m': TimeFrameUnit.Minute, '5m': TimeFrameUnit.Minute, '1m': TimeFrameUnit.Minute
        }

        frequency_mult = {
            'y': 1, 'q': 1, 'm': 1, 'w': 1, 'd': 1, '120m': 2, '60m': 1, '30m': 30, '15m': 15, '5m': 5, '1m': 1
        }

        timeframe = TimeFrame(frequency_mult[frequency], frequency_map[frequency])
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
                    start_date = (end_datetime - dt.timedelta(days=300)).strftime(time_format)
                elif frequency == 'd':
                    start_date = (end_datetime - dt.timedelta(days=750)).strftime(time_format)
                elif frequency == 'w':
                    start_date = (end_datetime - dt.timedelta(days=1200)).strftime(time_format)
                elif frequency == 'y':
                    start_date = (end_datetime - dt.timedelta(days=10000)).strftime(time_format)

            bars = self.api.get_bars(code.upper(), timeframe, start=start_date, limit=2400)
            if len(bars) != 0:
                df = bars.df
                # df['dt'] = pd.to_datetime(df['timestamp'], unit='ms')
                # df = df.set_index('dt')
                df = df.reset_index()
                klines = self.format_kline_pg(code, df)
                if frequency in {'y', 'q', 'm', 'w'}:
                    klines['date'] = klines['date'].apply(self.__convert_date)
                # klines = klines.sort_values('date')
                # klines = klines[['code', 'date', 'open', 'close', 'high', 'low', 'volume']]
                return klines
        except Exception as e:
            print(f'polygon.io 获取行情异常 {code} Exception ：{str(e)}')
        return None

    def stock_info(self, code: str) -> [Dict, None]:
        """
        获取股票名称，避免网络 api 请求，从 all_stocks 中获取
        """
        stocks = self.all_stocks()
        return next((s for s in stocks if s['code'] == code.upper()), None)
        # try:
        #     asset = self.api.get_asset(code)
        #     return {
        #         'code': asset.symbol,
        #         'name': asset.name
        #     }
        # except:
        #     return None

    def ticks(self, codes: List[str]) -> Dict[str, Tick]:
        """
        获取行情Tick数据
        """
        code_ticks = {}
        for code in codes:
            _tick = self.api.get_snapshot(code)
            code_ticks[code] = Tick(
                code=code,
                last=_tick.latest_trade.p,
                buy1=_tick.latest_quote.bp,
                sell1=_tick.latest_quote.ap,
                high=_tick.daily_bar.h,
                low=_tick.daily_bar.l,
                open=_tick.daily_bar.o,
                volume=_tick.daily_bar.v,
                rate=round((_tick.daily_bar.c - _tick.prev_daily_bar.c) / _tick.prev_daily_bar.c * 100, 2),
            )
        return code_ticks

    def now_trading(self):
        """
        返回当前是否是交易时间
        """
        try:
            clock = self.api.get_clock()
            if clock.is_open:
                return True
        except Exception:
            return False

    @staticmethod
    def __convert_date(_dt):
        _dt = fun.datetime_to_str(_dt, '%Y-%m-%d')
        return fun.str_to_datetime(_dt, '%Y-%m-%d')

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
