from __future__ import (absolute_import, division, print_function, unicode_literals)
import backtrader as bt
import backtrader.indicators as btind
          
          
class Bias(bt.Indicator):
    lines = ('Bias',)
    params = (('MA_period',20),)
    plotinfo = dict(subplot=True)
    plotlines = dict(Bias=dict( color="yellow", alpha=0.9))

    
    def __init__(self):
        print("Bias __init__")
        close = self.data.close 
        self.lines.Bias =(close/close)*400
        # super(Bias,self).__init__()
         