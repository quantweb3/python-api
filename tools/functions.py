import pymysql
import os
import tushare as ts  
import pandas as pd
from datetime import datetime, time
import platform
from sqlalchemy import create_engine
from urllib.parse import quote  
import configparser 
import backtrader as bt
from backtrader import plot
 
def getConfig():
  
    dir_path = os.path.dirname(os.path.realpath(__file__))
    cfgdir=os.path.abspath(os.path.join(dir_path, os.pardir))
    print(cfgdir)
    config = configparser.ConfigParser()
    config.read(os.path.join(cfgdir, 'config','config.ini' ))
    return config             
    

def getTushareToken():
    config = getConfig()
    print( config.get('tushare', 'tusharekey'))
    return  config.get('tushare', 'tusharekey')  

def getDbConn():
    config = getConfig()
    mydb = pymysql.connect(
    host= config.get('mysql', 'host'),
    user=config.get('mysql', 'user') ,
    password=config.get('mysql', 'password') ,
    db=config.get('mysql', 'db') ,
    autocommit=True,
    cursorclass=pymysql.cursors.DictCursor
    )
    return mydb             
    

def rootpath():
    config = getConfig()
    return  config.get('path', 'rootpath')  

def datapath():
    config = getConfig()
    return  config.get('path', 'datapath')  

def showDayDetail(record):
    print("当前日期:%s,开盘价格:%s ,收盘价格:%s ,交易量:%s" %(record.datetime.date(0),record.open[0],record.close[0],record.volume[0]))

def is_time_between( begin_time, end_time ):
    check_time =  datetime.now().time()
    print(check_time)
    if begin_time < end_time:
        return check_time >= begin_time and check_time <= end_time
    else: # crosses midnight
        return check_time >= begin_time or check_time <= end_time


def  isTradeHour():
     if is_time_between( time(9,30) ,time(11,30)) or is_time_between ( time(13,0) ,time(15,0)):
         return True;
     else: 
         return False



## 是否是交易时间
def ifTradeDay():
    
    ts.set_token(getTushareToken())
    pro = ts.pro_api()
    today = datetime.now().strftime('%Y%m%d')
    days = pro.query('trade_cal', start_date=today, end_date=today,is_open='1')
    # print(  len(days))
    if(len(days)==0):
        return False
    else :
        return True



def ifActiveMarketTime():
    
    ## 开发机不检查
    if 'macOS' in platform.platform():
        return True     
          
    if(  ifTradeDay() and  isTradeHour() ):
        return True 
    else :
        return False 
        
        
def printHuminfo():
    pass
    # portvalue = cerebro.broker.getvalue()
    # pnl = portvalue - startcash
    # #打印结果
    # print(f'初始: {round(startcash,2)}')
    # print(f'总资金: {round(portvalue,2)}')
    

def saveplots(cerebro,scheme, numfigs=1, iplot=True, start=None, end=None,
             width=16, height=9, dpi=300, tight=True, use=None, file_path = '', **kwargs):

        from backtrader import plot
        if cerebro.p.oldsync:
            plotter = plot.Plot_OldSync(**kwargs)
        else:
            plotter = plot.Plot( scheme=scheme, **kwargs)

        figs = []
        for stratlist in cerebro.runstrats:
            for si, strat in enumerate(stratlist):
                rfig = plotter.plot(strat, figid=si * 100,
                                    numfigs=numfigs, iplot=iplot,
                                    start=start, end=end, use=use)
                figs.append(rfig)

        for fig in figs:
            for f in fig:
                f.savefig(file_path, bbox_inches='tight')
        return figs
  