from fastapi import APIRouter, Depends
from fastapi.responses import JSONResponse
from fastapi.encoders import jsonable_encoder


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
 