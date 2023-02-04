from __future__ import (absolute_import, division, print_function, unicode_literals)
from fastapi import APIRouter, Depends
from fastapi.responses import JSONResponse
from fastapi.encoders import jsonable_encoder
from chanlun import rd, stock_dl_rank, kcharts, zixuan
from chanlun.exchange import get_exchange, Market
from django.http import HttpResponse
import jsonpickle
from . import utils
import os
import backtrader as bt
import pandas as pd
from datetime import datetime
from colorama import Fore, Back, Style
import sys
from pprint import pprint
from IPython.display import clear_output
import IPython
from IPython.display import display_html
from btplotting import BacktraderPlottingLive
from btplotting import BacktraderPlotting
from .TestStrategy import TestStrategy
import matplotlib 
matplotlib.rc("font", family='Microsoft YaHei')# 增加
sys.path.append("..")
from tools.debuger import *


bttest = APIRouter(
    
        # 这里配置的 tags、dependencies、responses 对这个模块的内的所有路径操作都生效
    # 路径前缀，该模块下所有路径操作的前缀
    prefix="/bttest",
    # 标签
    tags=["bttest"],
    # 响应
    responses={404: {"description": "bttest_router  found"}}
    
)

@bttest.post('/bttestChart')
async def bttestChart():
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'settings')
    # jsoutput= jsonpickle.encode( {"code":200,"stocks": []  } ,unpicklable=False )
    
    cerebro = bt.Cerebro()
    cerebro.addstrategy(TestStrategy )
    
    #获取数据
    
    data_files = '../books/'
    csv_name = 'sz000001.csv'

    ## current running file path 
    currentPath =os.path.dirname (os.path.realpath(__file__))
    stock_hfq_df = pd.read_csv(os.path.join( file_path,   'sz000001.csv'), index_col='date', parse_dates=True)
    
    
    start_date = datetime(2019, 8, 1)  # 回测开始时间
    end_date = datetime(2022, 8, 30)  # 回测结束时间
    data = bt.feeds.PandasData(dataname=stock_hfq_df, fromdate=start_date, todate=end_date)  # 加载数据
    cerebro.adddata(data)  # 将数据传入回测系统
    
        
    cerebro.broker.setcash(100)
    # cerebro.addanalyzer(BacktraderPlottingLive)
    cerebro.run()
    p = BacktraderPlotting(style='bar', output_mode='save', filename='tmphtml/abc.html' )
    # ,iplot=False,
    print("---show start-------->")
    print("--show end--------->")
    cerebro.plot(p , iplot=False)
    json_compatible_item_data = jsonable_encoder({"code":200,"filename":"aa"})
    return JSONResponse(content=json_compatible_item_data)

    
