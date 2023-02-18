import os
import sys
from fastapi import APIRouter, Depends
from fastapi.responses import JSONResponse
from fastapi.encoders import jsonable_encoder
from chanlun import rd, stock_dl_rank, kcharts, zixuan
from chanlun.cl_utils import web_batch_get_cl_datas, query_cl_chart_config, kcharts_frequency_h_l_map
from chanlun.exchange import get_exchange, Market
from django.http import HttpResponse
from tools.debuger import *
import tushare as ts  
sys.path.append("..")
from tools.functions import *
 

stock = APIRouter(
    # 这里配置的 tags、dependencies、responses 对这个模块的内的所有路径操作都生效
    # 路径前缀，该模块下所有路径操作的前缀
    prefix="/stock",
    # 标签
    tags=["stock"],
    # 响应
    responses={404: {"description": "stocks Not found"}}
)

  
 
# 搜索股票代码
@stock.post('/SearchStockCode')
def SearchStockCode(item: dict ):
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'settings')
    print(item)
    
    
    market = item['market']
    search = item['query']
    ex = get_exchange(Market(market))
    all_stocks = ex.all_stocks()
    debug(all_stocks)
    res = [
        stock for stock in all_stocks
        if search.lower() in stock['code'].lower() or search.lower() in stock['name'].lower()
    ]
    res = list({v['code']: v for v in res}.values())
    res_json = [{'code': r['code'], 'name': r['name']} for r in res]
    
    json_compatible_item_data = jsonable_encoder({"code":200,"stocks":res_json})
    return JSONResponse(content=json_compatible_item_data)

 
 
 # 搜索股票代码

def search_code_json(request):
    print(request)
    market = request.GET.get('market')
    print(f"search_code_json: {market}")
    search = request.GET.get('query')
    ex = get_exchange(Market(market))
    all_stocks = ex.all_stocks()
    res = [
        stock for stock in all_stocks
        if search.lower() in stock['code'].lower() or search.lower() in stock['name'].lower()
    ]
    print(type(res))
    #  get unqiue code from res
    res = list({v['code']: v for v in res}.values())
    res_json = [{'code': r['code'], 'name': r['name']} for r in res]
    return utils.response_as_json(res_json)
    
    
    # downloadTushare
    
@stock.post('/downloadTushare')
def downloadTushare(item: dict ):   
    code =item['code']
    
    # turn code from SZ.000282 to 000282.SZ
    code=code[3:]+"."+code[0:2]
    
    startdate=item['startdate']
    enddate=item['enddate']
    
    # remove - from  startdate
    startdate=startdate.replace("-","")
    enddate=enddate.replace("-","")
     
    # donwload data from tushare 
    
    ts.set_token(getTushareToken())
    pro = ts.pro_api()
    df = pro.query('daily', ts_code=code, start_date=startdate, end_date= enddate)
    # change ts_code to code in df
    
    df.sort_values(by="trade_date",axis=0,ascending=True,inplace=True)
    df.rename(columns={'trade_date':'date'}, inplace = True)
    df.to_csv('data/'+code+'.csv',index=False)
    
    
    
    json_compatible_item_data = jsonable_encoder({"code":200,"msg":"download success"})
    return JSONResponse(content=json_compatible_item_data)
    return utils.response_as_json(res_json)