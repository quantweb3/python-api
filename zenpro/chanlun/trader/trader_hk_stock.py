import datetime

from chanlun.exchange.exchange_futu import ExchangeFutu
from chanlun import rd, fun
from chanlun import zixuan
from chanlun.backtesting.base import Operation, POSITION
from chanlun.backtesting.backtest_trader import BackTestTrader

"""
使用富途的交易接口
"""


class TraderHKStock(BackTestTrader):
    """
    港股股票交易对象
    """

    def __init__(self, name, log=None):
        super().__init__(name=name, mode='real', is_stock=False, is_futures=False, log=log)

        self.ex = ExchangeFutu()

        self.b_space = 3  # 资金分割数量

        self.zx = zixuan.ZiXuan('hk')

    # 做多买入
    def open_buy(self, code, opt: Operation, amount: float = None):
        positions = self.ex.positions()
        if len(positions) >= self.b_space:
            return False
        stock_info = self.ex.stock_info(code)
        if stock_info is None:
            return False
        can_tv = self.ex.can_trade_val(code)
        if can_tv is None:
            return False
        max_amount = (can_tv['max_margin_buy'] / (self.b_space - len(positions)))
        max_amount = max_amount - (max_amount % stock_info['lot_size'])

        if max_amount == 0:
            return False
        order = self.ex.order(code, 'buy', max_amount)
        if order is False:
            fun.send_dd_msg('hk', f'{code} 下单失败 买入数量 {max_amount}')
            return False
        msg = f"股票买入 {code}-{stock_info['name']} 价格 {order['dealt_avg_price']} 数量 {order['dealt_amount']} 原因 {opt.msg}"

        fun.send_dd_msg('hk', msg)

        self.zx.add_stock('我的持仓', stock_info['code'], stock_info['name'])

        # 保存订单记录到 Redis 中
        save_order = {
            'code': code,
            'name': stock_info['name'],
            'datetime': fun.datetime_to_str(datetime.datetime.now()),
            'type': 'buy',
            'price': order['dealt_avg_price'],
            'amount': order['dealt_amount'],
            'info': opt.msg
        }
        rd.order_save('hk', code, save_order)

        return {'price': order['dealt_avg_price'], 'amount': order['dealt_amount']}

    # 做空卖出
    def open_sell(self, code, opt: Operation, amount: float = None):
        positions = self.ex.positions()
        if len(positions) >= self.b_space:
            return False
        stock_info = self.ex.stock_info(code)
        if stock_info is None:
            return False
        can_tv = self.ex.can_trade_val(code)
        if can_tv is None:
            return False
        max_amount = (can_tv['max_margin_short'] / (self.b_space - len(positions)))
        max_amount = max_amount - (max_amount % stock_info['lot_size'])
        if max_amount == 0:
            return False
        order = self.ex.order(code, 'sell', max_amount)
        if order is False:
            fun.send_dd_msg('hk', f'{code} 下单失败 卖出数量 {max_amount}')
            return False
        msg = f"股票卖空 {code}-{stock_info['name']} 价格 {order['dealt_avg_price']} 数量 {order['dealt_amount']} 原因 {opt.msg}"

        fun.send_dd_msg('hk', msg)

        self.zx.add_stock('我的持仓', stock_info['code'], stock_info['name'])

        # 保存订单记录到 Redis 中
        save_order = {
            'code': code,
            'name': stock_info['name'],
            'datetime': fun.datetime_to_str(datetime.datetime.now()),
            'type': 'sell',
            'price': order['dealt_avg_price'],
            'amount': order['dealt_amount'],
            'info': opt.msg
        }
        rd.order_save('hk', code, save_order)

        return {'price': order['dealt_avg_price'], 'amount': order['dealt_amount']}

    # 做多平仓
    def close_buy(self, code, pos: POSITION, opt: Operation):
        positions = self.ex.positions(code)
        if len(positions) == 0:
            return {'price': pos.price, 'amount': pos.amount}

        stock_info = self.ex.stock_info(code)
        if stock_info is None:
            return False

        order = self.ex.order(code, 'sell', pos.amount)
        if order is False:
            fun.send_dd_msg('hk', f'{code} 下单失败 平仓卖出 {pos.amount}')
            return False
        msg = '股票卖出 %s-%s 价格 %s 数量 %s 盈亏 %s (%.2f%%) 原因 %s' % (
            code, stock_info['name'], order['dealt_avg_price'], order['dealt_amount'], positions[0]['profit_val'],
            positions[0]['profit'],
            opt.msg)
        fun.send_dd_msg('hk', msg)

        self.zx.del_stock('我的持仓', stock_info['code'])

        # 保存订单记录到 Redis 中
        save_order = {
            'code': code,
            'name': stock_info['name'],
            'datetime': fun.datetime_to_str(datetime.datetime.now()),
            'type': 'sell',
            'price': order['dealt_avg_price'],
            'amount': order['dealt_amount'],
            'info': opt.msg
        }
        rd.order_save('hk', code, save_order)

        return {'price': order['dealt_avg_price'], 'amount': order['dealt_amount']}

    # 做空平仓
    def close_sell(self, code, pos: POSITION, opt: Operation):
        positions = self.ex.positions(code)
        if len(positions) == 0:
            return {'price': pos.price, 'amount': pos.amount}

        stock_info = self.ex.stock_info(code)
        if stock_info is None:
            return False

        order = self.ex.order(code, 'buy', pos.amount)
        if order is False:
            fun.send_dd_msg('hk', f'{code} 下单失败 平仓买入 {pos.amount}')
            return False
        msg = '股票平空 %s-%s 价格 %s 数量 %s 盈亏 %s (%.2f%%) 原因 %s' % (
            code, stock_info['name'], order['dealt_avg_price'], order['dealt_amount'], positions[0]['profit_val'],
            positions[0]['profit'],
            opt.msg)
        fun.send_dd_msg('hk', msg)

        self.zx.del_stock('我的持仓', stock_info['code'])

        # 保存订单记录到 Redis 中
        save_order = {
            'code': code,
            'name': stock_info['name'],
            'datetime': fun.datetime_to_str(datetime.datetime.now()),
            'type': 'buy',
            'price': order['dealt_avg_price'],
            'amount': order['dealt_amount'],
            'info': opt.msg
        }
        rd.order_save('hk', code, save_order)

        return {'price': order['dealt_avg_price'], 'amount': order['dealt_amount']}
