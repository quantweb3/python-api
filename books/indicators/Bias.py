from __future__ import (absolute_import, division, print_function, unicode_literals)
import backtrader as bt
import backtrader.indicators as btind
          
          
class Bias(bt.Indicator):
    lines = ('Bias',)
    params = (('MA_period',20),)
    plotinfo = dict(subplot=True)
    # plotlines = dict(Bias=dict(_fill_gt('Bias', ('yellow', 0.50))))
    
    plotlines = dict(
        senkou_span_a=dict(_fill_gt=('senkou_span_b', 'g'),
                           _fill_lt=('senkou_span_b', 'r')),
    )
    
    plotlines = dict(Bias=dict( color="yellow", alpha=0.9))

    
    def __init__(self):
        print("Bias __init__")
        close = self.data.close 
        self.lines.Bias =(close/close)*400
        # super(Bias,self).__init__()
         