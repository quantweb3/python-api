from __future__ import (absolute_import, division, print_function,
                        unicode_literals)

import backtrader as bt
import backtrader.indicators as btind


class MyTrix(bt.Indicator):

    lines = ('trix',)
    params = (('period', 15),)

    def __init__(self):
        #   ema1 = btind.EMA(self.data, period=self.p.period)
        #   ema2 = btind.EMA(ema1, period=self.p.period)
        #   ema3 = btind.EMA(ema2, period=self.p.period)

          self.trix = 100.0  ;