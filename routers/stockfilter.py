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
import os
import sys


stockfilter = APIRouter(
    # 这里配置的 tags、dependencies、responses 对这个模块的内的所有路径操作都生效
    # 路径前缀，该模块下所有路径操作的前缀
    prefix="/stockfilter",
    # 标签
    tags=["stockfilter"],
  
    # 响应
    responses={404: {"description": "stocks Not found"}}
)


@stockfilter.post('/filter213')
async def filter213():
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'settings')
    filter213=StockFilter213({})
    filter213.filterAll().saveFilterResult()
    jsoutput= jsonpickle.encode( {"code":200,"stocks":  filter213.filterResults  } ,unpicklable=False )
    return jsoutput 



## 筛选:三低
@stockfilter.post('/filterThreeLow',tags=["stockfilter"])
def filterThreeLow():
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'settings')
    filter3D=StockFilterThreeDown({})
    filter3D.filterAll().saveFilterResult()
    jsoutput= jsonpickle.encode( {"code":200,"stocks":  filter3D.filterResults  } ,unpicklable=False )
    return jsoutput     
    
 
## 筛选:三低 高开低走巨阴
@stockfilter.post('/filterOpenHighCloseLowVolUp')
def filterOpenHighCloseLowVolUp( item: dict ):
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'settings')
    filterHLV=StockFilterHIghLowVolUp(item)
    filterHLV.filterAll().saveFilterResult()
    jsoutput= jsonpickle.encode( {"code":200,"stocks":filterHLV.filterResults} ,unpicklable=False )
    print(jsoutput)
    return jsoutput 

    