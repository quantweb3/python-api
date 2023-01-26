from typing import Union

from gm.api import *
from tenacity import retry, stop_after_attempt, wait_random, retry_if_result

from chanlun import config
from chanlun import rd
from chanlun.exchange.exchange import *
from chanlun.exchange.exchange_tdx import ExchangeTDX

g_all_stocks = []
g_trade_days = None


class ExchangeGMA(Exchange):
    """
    掘金A股数据接口

    TODO 获取数据太慢，暂时不可使用
    """

    def __init__(self):
        set_serv_addr(config.GM_SERVER_ADDR)
        set_token(config.GM_TOKEN)

        self.ex_tdx = ExchangeTDX()

    def all_stocks(self):
        """
        通过掘金 API 获取所有 股票/指数/基金代码
        """
        global g_all_stocks
        if len(g_all_stocks) > 0:
            return g_all_stocks
        stocks = get_instruments(
            symbols=None, exchanges=['SHSE', 'SZSE'], sec_types=[SEC_TYPE_STOCK, SEC_TYPE_FUND, SEC_TYPE_INDEX]
        )
        for s in stocks:
            g_all_stocks.append(
                {'code': s['symbol'].replace('SZSE', 'SZ').replace('SHSE', 'SH'), 'name': s['sec_name']}
            )

        return g_all_stocks

    @retry(stop=stop_after_attempt(3), wait=wait_random(min=1, max=5), retry=retry_if_result(lambda _r: _r is None))
    def klines(self, code: str, frequency: str,
               start_date: str = None, end_date: str = None,
               args=None) -> Union[pd.DataFrame, None]:

        """
        暂不支持按时间获取
        """

        # 年/季/月/周，使用 通达信 获取
        if frequency in ['y', 'q', 'm', 'w', 'd']:
            return self.ex_tdx.klines(code, frequency, start_date, end_date, args)

        # 将任务添加到 redis 队列，之后就等着获取
        redis_obj = rd.Robj()
        gm_code = code.replace('SZ', 'SZSE').replace('SH', 'SHSE')
        sync_key = f'{gm_code}:{frequency}'
        data_key = f'gm_{gm_code}:{frequency}'
        # 手动删除下数据 key，避免获取旧的数据
        redis_obj.delete(data_key)
        redis_obj.lpush('gm_sync', f'{gm_code}:{frequency}')
        for i in range(10):
            klines_json = redis_obj.get(data_key)
            if klines_json is None:
                time.sleep(1)
                continue
            klines = pd.read_json(klines_json, orient='split')
            return klines
        return None

    def stock_info(self, code: str) -> Union[Dict, None]:
        """
        获取股票名称
        """
        all_stock = self.all_stocks()
        stock = [_s for _s in all_stock if _s['code'] == code]
        if not stock:
            return None
        return {
            'code': stock[0]['code'],
            'name': stock[0]['name']
        }

    def ticks(self, codes: List[str]) -> Dict[str, Tick]:
        """
        使用原 tdx 的接口
        """
        return self.ex_tdx.ticks(codes)

    def now_trading(self):
        """
        返回当前是否是交易时间
        """
        return self.ex_tdx.now_trading()

    def stock_owner_plate(self, code: str):
        """
        使用富途的服务
        """
        return self.ex_tdx.stock_owner_plate(code)

    def plate_stocks(self, code: str):
        """
        使用富途的服务
        """
        return self.ex_tdx.plate_stocks(code)

    def balance(self):
        raise Exception('交易所不支持')

    def positions(self, code: str = ''):
        raise Exception('交易所不支持')

    def order(self, code: str, o_type: str, amount: float, args=None):
        raise Exception('交易所不支持')
