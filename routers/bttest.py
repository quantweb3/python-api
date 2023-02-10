from __future__ import (absolute_import, division, print_function, unicode_literals)
import os,sys,random
from fastapi import APIRouter, Depends
from fastapi.responses import JSONResponse
from fastapi.encoders import jsonable_encoder
from django.http import HttpResponse
import backtrader as bt
import pandas as pd
from datetime import datetime
import IPython   
from btplotting import BacktraderPlottingLive
from btplotting import BacktraderPlotting
import matplotlib 
sys.path.append("..")
from strategy.TestStrategy import TestStrategy
from strategy.SMA20Strategy import SMA20Strategy
from tools.functions import *
from tools.debuger import *
import quantstats



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
    # join path and filename
    csv_name = datapath()+'/600519.SH.csv'
    
    
    stock_hfq_df = pd.read_csv( csv_name, index_col='date', parse_dates=True)
    # printtable(stock_hfq_df)
    # return 1;
    #添加策略
    # cerebro.addstrategy(TestStrategy )
    cerebro.addstrategy(SMA20Strategy )
    
    start_date = datetime(2019, 1, 1)  # 回测开始时间
    end_date = datetime(2019, 12, 31)  # 回测结束时间
    data = bt.feeds.PandasData(dataname=stock_hfq_df, fromdate=start_date, todate=end_date)  # 加载数据
    
    cerebro.adddata(data)  # 将数据传入回测系统
    startcash=10000
    cerebro.broker.setcash(startcash)
    # cerebro.addanalyzer(BacktraderPlottingLive)
    # cerebro.addanalyzer(BacktraderPlotting)
    
    cerebro.addanalyzer(bt.analyzers.PyFolio , _name='pyfolio')

    # generate random file name by date 
    filename=  datetime.now().strftime("%Y%m%d%H%M%S")+ str(random.randint(100000,999999))
    pngname  = f'tmphtml/{filename}.png'
    btplotting_htmlname = f'tmphtml/btplotting_{filename}.html'
    quantstats_htmlname = f'tmphtml/quantstats_{filename}.html'
    
    
    
    strats = cerebro.run()
    strat0 = strats[0]
    pyProfile = strat0.analyzers.getbyname('pyfolio')
    returns, positions, transactions, gross_lev = pyProfile.get_pf_items() 
    print('---------->')
    debug(returns)
    printtable(returns)
    # printtable(transactions)
    # printtable(gross_lev)
    returns.index = returns.index.tz_convert(None)
    quantstats.reports.html(returns,  download_filename= quantstats_htmlname , output= True, title='分析报告')
    
    scheme = bt.plot.PlotScheme()
    scheme.grid=False
    scheme.subtxtsize =44 
        
    
     
    
    
    
    # save orginal plot to png 
    saveplots(cerebro,scheme ,volume=False, file_path =pngname) #run it
    
    # save using BacktraderPlotting
    p = BacktraderPlotting(style='bar', output_mode='save', filename=btplotting_htmlname )
    cerebro.plot(p , iplot=False)
        
    # replace htmlname substirng tmphtml to public
    json_compatible_item_data = jsonable_encoder(
        {"code":200,
        "btplotting_htmlname":btplotting_htmlname.replace('tmphtml','public'),
        "quantstats_htmlname":quantstats_htmlname.replace('tmphtml','public'),
        "pngname": pngname.replace('tmphtml','public')}
        )
    return JSONResponse(content=json_compatible_item_data)

    
    
