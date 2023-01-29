from fastapi import APIRouter, Depends
from fastapi.responses import JSONResponse
from fastapi.encoders import jsonable_encoder
from chanlun import rd, stock_dl_rank, kcharts, zixuan
from chanlun.cl_utils import web_batch_get_cl_datas, query_cl_chart_config, kcharts_frequency_h_l_map
from chanlun.exchange import get_exchange, Market
from django.http import HttpResponse
from filter.StockFilterThreeDown import StockFilterThreeDown
from filter.StockFilterHIghLowVolUp import StockFilterHIghLowVolUp
from filter.StockFilter213 import StockFilter213
import jsonpickle
from . import utils
import os
import sys


stockfilter_router = APIRouter(
    # 这里配置的 tags、dependencies、responses 对这个模块的内的所有路径操作都生效
    # 路径前缀，该模块下所有路径操作的前缀
    prefix="/stockfilter",
    # 标签
    tags=["stockfilter"],
  
    # 响应
    responses={404: {"description": "stocks Not found"}}
)


@stockfilter_router.post('/filter213')
async def filter213():
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'settings')
    filter213=StockFilter213({})
    filter213.filterAll().saveFilterResult()
    jsoutput= jsonpickle.encode( {"code":200,"stocks":  filter213.filterResults  } ,unpicklable=False )
    return jsoutput 
    