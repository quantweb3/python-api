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

class TestStrategy(bt.Strategy):
    #  策略参数
    params = (
        
        ('defaultSize',100),
        ('printlog', True),
        ('bias_period',20),  # Bias指标周期
    )
    
   

    def log(self, txt, dt=None):
        ''' 记录功能'''
        dt = dt or self.datas[0].datetime.date(0)
        # print('%s, %s' % (dt.isoformat(), txt))

    def __init__(self):
        
        print("TestStrategy __init   &&&&&")
        self.bias = Bias( self.data,subplot=True, plotforce=True,  plotabove=True, plotname="指标1",MA_period=self.p.bias_period)

        # 引用到数据的close Line
        self.dataclose = self.datas[0].close
       
        # printtable( self.datas[0]._dataname )

        
        # 跟踪订单
        self.order = None
        
      

    def notify_order(self, order):
        if order.status in [order.Submitted, order.Accepted]:
            # 订单提交和成交当前不做处理
            return
        
        # pprint(order)
        # self.log('OPERATION PROFIT, GROSS  NET %.2f' %
        #          ( order.pnlcomm))    

        # 检查订单是否成交
        # 注意，如果现金不够的话，订单会被拒接
        if order.status in [order.Completed]:
            if order.isbuy():
                print(Fore.RED + '>>>>>>>>>>')
                self.log('>>>>>>>>>> 买入被执行 买入价格, %.2f' % order.executed.price)
                print('当前可用资金', self.broker.getcash())
                print('当前总资产', self.broker.getvalue())
                print('当前持仓量', self.broker.getposition(self.data).size)
                print('当前持仓成本', self.broker.getposition(self.data).price)
                print(Fore.RED + '<<<<<<<<<<<<<')
                print(Style.RESET_ALL)

                
                
            elif order.issell():
                self.log('卖出被执行,卖出价格, %.2f' % order.executed.price)

            self.bar_executed = len(self)

        elif order.status in [order.Canceled, order.Margin, order.Rejected]:
            print('订单取消 Order Canceled/Margin/Rejected' , order.status)
            if  order.status in [order.Canceled]:
                print('订单取消 Order Canceled' , order.status)
            if  order.status in [order.Margin]:
                print('订单取消 Order Margin' , order.status)
            if  order.status in [order.Rejected]:
                print('订单取消 Order Rejected' , order.status)    
                
            

        # 记录没有挂起的订单
        self.order = None

    def next(self):
        curdate = self.datas[0].datetime.date(0)
        # print("SMA",curdate, self.sma[0]) ;
        # 也可以直接获取持仓
        # print('当前持仓量', self.getposition(self.data).size)
        # print('当前持仓成本', self.getposition(self.data).price)
        #记录close的价格
        # self.log('Close, %.2f' % self.dataclose[0])

        # 检查是否有挂起的订单，如果有的话，不能再发起一个订单
        if self.order:
            return

        # 检查是否在市场（有持仓）
        if not self.position:
            
             curdate = self.datas[0].datetime.date(0)
            #  print('当前日期, %s' % curdate)
        
             if curdate == datetime.strptime('2019-08-01', '%Y-%m-%d').date():
                 print("good day")
                 # 可以买的最大数量????????????  
                 self.order = self.buy( size=self.params.defaultSize   )

            # 不在，那么连续3天价格下跌就买点
            # if self.dataclose[0] < self.dataclose[-1]:
            #         # 当前价格比上一次低

            #         if self.dataclose[-1] < self.dataclose[-2]:
            #             # 上一次的价格比上上次低
            #             # 买入!!! 
            #             self.log('买入创建, %.2f' % self.dataclose[0])

            #             # Keep track of the created order to avoid a 2nd order
            #             self.order = self.buy()

        else:

            # 已经在市场，5天后就卖掉。
            if len(self) >= (self.bar_executed + 5):#这里注意，Len(self)返回的是当前执行的bar数量，每次next会加1.而Self.bar_executed记录的最后一次交易执行时的bar位置。
                # SELL, SELL, SELL!!! (with all possible default parameters)
                # self.log('卖出 CREATE, %.2f' % self.dataclose[0])
                self.log('do nothing')
                 
                # Keep track of the created order to avoid a 2nd order
                # self.order = self.sell(size=10)
