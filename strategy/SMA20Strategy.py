# 从未来导入绝对导入，除法，打印功能，unicode_literals
from __future__ import (absolute_import, division, print_function, unicode_literals)
import backtrader as bt
import pandas as pd
from datetime import datetime
from colorama import Fore, Back, Style
import sys
from pprint import pprint
sys.path.append("..")
from tools.debuger import *
sys.path.append("..")
from indicators.Bias import Bias


class SMA20Strategy(bt.Strategy):
    params = (
        ('m', 20),
    )

    def log(self, txt, dt=None):
        pass
        # df = self.datas[0].datetime.date(0)
        # print('%s, %s' % (df.isoformat(), txt))

    def __init__(self):
        self.dataclose = self.datas[0].close

        self.sma = bt.indicators.SMA(self.datas[0], period=self.params.m)

        self.order = None

    def notify_order(self, order):
        if order.status in [order.Submitted, order.Accepted]:
            # Buy/Sell order submitted/accepted to/by broker - Nothing to do
            return

        # Check if an order has been completed
        # Attention: broker could reject order if not enough cash
        if order.status in [order.Completed]:
            if order.isbuy():
                self.log('BUY EXECUTED, %.2f' % order.executed.price)
            elif order.issell():
                self.log('SELL EXECUTED, %.2f' % order.executed.price)

            self.bar_executed = len(self)
            
            # print('=======order',self.bar_executed)

        elif order.status in [order.Canceled, order.Margin, order.Rejected]:
            self.log('Order Canceled/Margin/Rejected')

        # Write down: no pending order
        self.order = None


    def next(self):
        if self.order:
            self.log("==is order: %s" % self.order)
            return

        # 检查是否持仓
        if not self.position:
            # 上涨突破20日均线执行买入
            if self.dataclose[0] > self.sma[0]:
                self.log('BUY CREATE, %.2f' % self.dataclose[0])
                self.order = self.buy()
        else:
            # 下跌突破20日均线执行卖出
            if self.dataclose[0] < self.sma[0]:
                self.log('SELL CREATE, %.2f' % self.dataclose[0])
                self.order = self.sell()
