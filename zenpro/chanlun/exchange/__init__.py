from enum import Enum
from chanlun import config

from chanlun.exchange.exchange import Exchange
from chanlun.exchange.exchange_tdx import ExchangeTDX
from chanlun.exchange.exchange_futu import ExchangeFutu
from chanlun.exchange.exchange_baostock import ExchangeBaostock
from chanlun.exchange.exchange_tq import ExchangeTq
from chanlun.exchange.exchange_binance import ExchangeBinance
from chanlun.exchange.exchange_zb import ExchangeZB
from chanlun.exchange.exchange_polygon import ExchangePolygon
from chanlun.exchange.exchange_alpaca import ExchangeAlpaca

# 全局保存交易所对象，避免创建多个交易所对象
g_exchange_obj = {}


class Market(Enum):
    """
    交易市场
    """
    A = 'a'
    HK = 'hk'
    FUTURES = 'futures'
    CURRENCY = 'currency'
    US = 'us'


def get_exchange(market: Market) -> Exchange:
    """
    获取市场的交易所对象，根据config配置中设置的进行获取
    """
    global g_exchange_obj
    if market.value in g_exchange_obj.keys():
        return g_exchange_obj[market.value]

    if market == Market.A:
        # 沪深 A股 交易所
        print("++++++++++++++")
        print(config.EXCHANGE_A)
        
        if config.EXCHANGE_A == 'tdx':
            g_exchange_obj[market.value] = ExchangeTDX()
        elif config.EXCHANGE_A == 'futu':
            g_exchange_obj[market.value] = ExchangeFutu()
        elif config.EXCHANGE_A == 'baostock':
            g_exchange_obj[market.value] = ExchangeBaostock()
        else:
            raise Exception(f'不支持的沪深交易所 {config.EXCHANGE_A}')

    elif market == Market.HK:
        # 港股 交易所
        if config.EXCHANGE_HK == 'futu':
            g_exchange_obj[market.value] = ExchangeFutu()
        else:
            raise Exception(f'不支持的香港交易所 {config.EXCHANGE_HK}')

    elif market == Market.FUTURES:
        # 期货 交易所
        if config.EXCHANGE_FUTURES == 'tq':
            g_exchange_obj[market.value] = ExchangeTq()
        else:
            raise Exception(f'不支持的期货交易所 {config.EXCHANGE_FUTURES}')

    elif market == Market.CURRENCY:
        # 数字货币 交易所
        if config.EXCHANGE_CURRENCY == 'binance':
            g_exchange_obj[market.value] = ExchangeBinance()
        elif config.EXCHANGE_CURRENCY == 'zb':
            g_exchange_obj[market.value] = ExchangeZB()
        else:
            raise Exception(f'不支持的数字货币交易所 {config.EXCHANGE_CURRENCY}')

    elif market == Market.US:
        # 美股 交易所
        if config.EXCHANGE_US == 'alpaca':
            g_exchange_obj[market.value] = ExchangeAlpaca()
        elif config.EXCHANGE_US == 'polygon':
            g_exchange_obj[market.value] = ExchangePolygon()
        else:
            raise Exception(f'不支持的美股交易所 {config.EXCHANGE_US}')

    return g_exchange_obj[market.value]
