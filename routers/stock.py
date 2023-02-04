from fastapi import APIRouter, Depends
from fastapi.responses import JSONResponse
from fastapi.encoders import jsonable_encoder
from chanlun import rd, stock_dl_rank, kcharts, zixuan
from chanlun.cl_utils import web_batch_get_cl_datas, query_cl_chart_config, kcharts_frequency_h_l_map
from chanlun.exchange import get_exchange, Market
from django.http import HttpResponse
from . import utils
import os
import sys


stock_router = APIRouter(
    # 这里配置的 tags、dependencies、responses 对这个模块的内的所有路径操作都生效
    # 路径前缀，该模块下所有路径操作的前缀
    prefix="/stock",
    # 标签
    tags=["stock"],
    # 响应
    responses={404: {"description": "stocks Not found"}}
)


@stock_router.post('/kline',tags=['stock'])
async def kline(item: dict):
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'settings')
    code=item['code']
    print(code)
    frequencys=item['frequencys']
    print(frequencys)
    # loop frequencys to create charts
    
    charts=[]
    for frequency in frequencys:
        chart = await CreateOneStockZenChart(code,frequency)
        charts.append(chart)
    
    json_compatible_item_data = jsonable_encoder({"code":200,"charts":charts})
    return JSONResponse(content=json_compatible_item_data)
 
 


async def CreateOneStockZenChart(code,frequency):

    # 如果开启并设置的该级别的低级别数据，获取低级别数据，并在转换成高级图表展示
    frequency_low, kchart_to_frequency = kcharts_frequency_h_l_map('a', frequency)
    frequency_new = frequency_low if frequency_low else frequency
    pages = 12 if frequency_low else 8  # 如果用低级别大数据合并高级别，就获取多些数据

    cl_chart_config = query_cl_chart_config('a', code)
    ex = get_exchange(Market.A)
    klines = ex.klines(code, frequency=frequency_new, args={'pages': pages})
    
    cd = web_batch_get_cl_datas('a', code, {frequency_new: klines}, cl_chart_config, )[0]
    stock_info = ex.stock_info(code)
    orders = rd.order_query('a', code)
    
    title = stock_info['code'] + ':' + stock_info['name'] + ':' + (
        f'{frequency_low}->{frequency}' if frequency_low else frequency)
    chart = kcharts.render_charts(
        title, cd, to_frequency=kchart_to_frequency, orders=orders, config=cl_chart_config)
    return {"code":code, "frequency":frequency, "chart":chart} 
 

 





 
# 搜索股票代码
@stock_router.post('/SearchStockCode')
def SearchStockCode(item: dict ):
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'settings')
    print(item)
    
    
    market = item['market']
    search = item['query']
    ex = get_exchange(Market(market))
    all_stocks = ex.all_stocks()
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
    # print(all_stocks)
    res = [
        stock for stock in all_stocks
        if search.lower() in stock['code'].lower() or search.lower() in stock['name'].lower()
    ]
    print(type(res))
    #  get distinct code from res
    res = list({v['code']: v for v in res}.values())
    res_json = [{'code': r['code'], 'name': r['name']} for r in res]
    return utils.response_as_json(res_json)