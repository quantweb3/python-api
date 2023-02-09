from __future__ import (absolute_import, division, print_function, unicode_literals)
import os,sys
from fastapi import APIRouter, Depends
from fastapi.responses import JSONResponse
from fastapi.encoders import jsonable_encoder
from django.http import HttpResponse
import backtrader as bt
import pandas as pd
import random
from datetime import datetime
import IPython   
from btplotting import BacktraderPlottingLive
from btplotting import BacktraderPlotting
from tools.functions import saveplots
import matplotlib 
sys.path.append("..")
from strategy.TestStrategy import TestStrategy


matplotlib.rc("font", family='Microsoft YaHei')# 增加


bttest = APIRouter(
    prefix="/bttest",
    tags=["bttest"],
    responses={404: {"description": "404"}}
)


@bttest.post('/bttestChart')
async def bttestChart():
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'settings')
    cerebro = bt.Cerebro()
    
    #获取数据
    ## current running file path 
    currentPath =os.path.dirname (os.path.realpath(__file__))
    ## get parent path from current path
    parentPath = os.path.dirname(currentPath)
    csv_name = 'sz000001.csv'
    stock_hfq_df = pd.read_csv(os.path.join( parentPath, 'data/', csv_name), index_col='date', parse_dates=True)

    #添加策略
    cerebro.addstrategy(TestStrategy )
    
    
    start_date = datetime(2019, 8, 1)  # 回测开始时间
    end_date = datetime(2022, 8, 30)  # 回测结束时间
    data = bt.feeds.PandasData(dataname=stock_hfq_df, fromdate=start_date, todate=end_date)  # 加载数据
    
    cerebro.adddata(data)  # 将数据传入回测系统
    startcash=10000
    cerebro.broker.setcash(startcash)
    # cerebro.addanalyzer(BacktraderPlottingLive)
    # cerebro.addanalyzer(BacktraderPlotting)
    
    cerebro.run()
    
    # generate random file name by date 
    filename=  datetime.now().strftime("%Y%m%d%H%M%S")+ str(random.randint(100000,999999))
    
    
    #  f-string  add .png to filename
    pngname  = f'tmphtml/{filename}.png'
    htmlname = f'tmphtml/{filename}.html'
     
    saveplots(cerebro, file_path =pngname) #run it
    p = BacktraderPlotting(style='bar', output_mode='save', filename=htmlname )
    cerebro.plot(p , iplot=False)
        
    # replace htmlname substirng tmphtml to public
    json_compatible_item_data = jsonable_encoder({"code":200,"htmlname":htmlname.replace('tmphtml','public'),"pngname": pngname.replace('tmphtml','public')})
    return JSONResponse(content=json_compatible_item_data)

    
    
