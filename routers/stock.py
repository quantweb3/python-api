from fastapi import APIRouter, Depends
from fastapi.responses import JSONResponse
from fastapi.encoders import jsonable_encoder
from chanlun import rd, stock_dl_rank, kcharts, zixuan
from chanlun.cl_utils import web_batch_get_cl_datas, query_cl_chart_config, kcharts_frequency_h_l_map
from chanlun.exchange import get_exchange, Market
from django.http import HttpResponse
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

 


@stock_router.get('/list/')
async def list():
    stocks=[{"id":1, "name":"苹果","price":100},{"id":2,"name":"Google","price":200},{"id":3,"name":"Microsoft","price":300}]
    obj = jsonable_encoder(  {"code":200,"stocks": stocks }  )
    return JSONResponse(obj)


@stock_router.post('/kline')

async def kline(item: dict):
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'settings')
    
    code='SH.000001'
    code=item['code']
    print("==========>Code")
    print(code)
    
    frequency=item['frequency']
    print("==========>frequency")
    print(frequency)

    # 如果开启并设置的该级别的低级别数据，获取低级别数据，并在转换成高级图表展示
    frequency_low, kchart_to_frequency = kcharts_frequency_h_l_map('a', frequency)
    frequency_new = frequency_low if frequency_low else frequency
    pages = 12 if frequency_low else 8  # 如果用低级别大数据合并高级别，就获取多些数据

    cl_chart_config = query_cl_chart_config('a', code)
    ex = get_exchange(Market.A)
    klines = ex.klines(code, frequency=frequency_new, args={'pages': pages})
    print("============K线数据===========")
    print(klines)
    
    cd = web_batch_get_cl_datas('a', code, {frequency_new: klines}, cl_chart_config, )[0]
    stock_info = ex.stock_info(code)
    print("============stock_info===========")
    print(stock_info)
    orders = rd.order_query('a', code)
    print("============orders===========")
    print(orders)
    
    title = stock_info['code'] + ':' + stock_info['name'] + ':' + (
        f'{frequency_low}->{frequency}' if frequency_low else frequency)
    chart = kcharts.render_charts(
        title, cd, to_frequency=kchart_to_frequency, orders=orders, config=cl_chart_config)
    # print(chart)
    # print the type of chart
    print(type(chart)) 
    print(chart[:100])
    # get char length
    print(len(chart))
    return HttpResponse(chart)


 