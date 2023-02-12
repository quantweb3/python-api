from __future__ import (absolute_import, division, print_function, unicode_literals)
import os,sys,random
from fastapi import APIRouter, Depends
from fastapi.responses import JSONResponse
from fastapi.encoders import jsonable_encoder
from django.http import HttpResponse
import backtrader as bt
from pathlib import Path
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
import importlib



matplotlib.rc("font", family='Microsoft YaHei')# 增加
bttest = APIRouter(
    prefix="/bttest",
    tags=["bttest"],
    responses={404: {"description": "404"}}
)


def saveResult(cerebro,strats):
    
    ## delete files in tmphtml not today created
    today = datetime.now().strftime("%Y%m%d")
    for file in os.listdir('tmphtml'):
        if today not in file:
                os.remove(os.path.join('tmphtml', file))
    
    # generate random file name by date 
    filename=  datetime.now().strftime("%Y%m%d%H%M%S")+ str(random.randint(100000,999999))
    pngname  = f'tmphtml/{filename}.png'
    btplotting_htmlname = f'tmphtml/btplotting_{filename}.html'
    quantstats_htmlname = f'tmphtml/quantstats_{filename}.html'
    
    strat0 = strats[0]
    pyProfile = strat0.analyzers.getbyname('pyfolio')
    returns, positions, transactions, gross_lev = pyProfile.get_pf_items() 
  
    returns.index = returns.index.tz_convert(None)
    quantstats.reports.html(returns,  download_filename= quantstats_htmlname , output= True, title='分析报告')
    
    scheme = bt.plot.PlotScheme()
    scheme.grid=True
    scheme.width=40
    scheme.height=20
        
    
    # save orginal plot to png 
    saveplots(cerebro,scheme ,volume=False, file_path =pngname) #run it
    
    # save using BacktraderPlotting
    p = BacktraderPlotting(style='bar', output_mode='save', filename=btplotting_htmlname )
    cerebro.plot(p , iplot=False)
    
    btplotting_htmlname=btplotting_htmlname.replace('tmphtml','public')
    quantstats_htmlname=quantstats_htmlname.replace('tmphtml','public')
    pngname= pngname.replace('tmphtml','public')
    return {"pngname": pngname, "btplotting_htmlname":btplotting_htmlname,"quantstats_htmlname":quantstats_htmlname  }
    

def getMarkDown(strategyName):
     
    x=Path('strategy')
    markdownFile = os.path.join(x, strategyName+'.md')
    # read content from markdownFile
    if os.path.exists(markdownFile):
        with open(markdownFile, 'r', encoding='utf-8') as f:
            markdownStr = f.read()
    else:
        markdownStr = None
    return markdownStr

@bttest.post('/getStrategyList')
async def getStrategyList():
    x=Path('strategy')
    strategyList=list(filter(lambda y:y.is_file() and  y.suffix in ['.py'], x.iterdir()))
    strategyList = [  str(item).replace('strategy/','').replace('.py', '')  for item in strategyList]
    
    ## transform strategyList to array of object with name and key
    strategyList = [ {"label": item, "value":item, "markdown": getMarkDown(item)} for item in strategyList]
    
     
    json_compatible_item_data = jsonable_encoder(
        {"code":200, "strategyList": strategyList } )
    return JSONResponse(content=json_compatible_item_data)

@bttest.post('/bttestChart')
async def bttestChart():
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'settings')
    cerebro = bt.Cerebro()
    
    #获取数据
    # join path and filename
    csv_name = datapath()+'/600519.SH.csv'
    
    
    stock_hfq_df = pd.read_csv( csv_name, index_col='date', parse_dates=True)
    cerebro.addstrategy(SMA20Strategy )
    
    start_date = datetime(2019, 1, 1)  # 回测开始时间
    end_date = datetime(2019, 12, 31)  # 回测结束时间
    data = bt.feeds.PandasData(dataname=stock_hfq_df, fromdate=start_date, todate=end_date)  # 加载数据
    
    cerebro.adddata(data)  # 将数据传入回测系统
    startcash=10000
    cerebro.broker.setcash(startcash)
    
    cerebro.addanalyzer(bt.analyzers.PyFolio , _name='pyfolio')
    cerebro.addanalyzer(bt.analyzers.TimeDrawDown, _name='回撤')
    cerebro.addobserver(bt.observers.DrawDown )
    cerebro.addobserver(bt.observers.Benchmark )
    cerebro.addobserver(bt.observers.TimeReturn )
    strats = cerebro.run()
    tmp=   saveResult(cerebro,strats)
    json_compatible_item_data = jsonable_encoder(
        {"code":200, "btresult":tmp} )
    return JSONResponse(content=json_compatible_item_data)

    
    
