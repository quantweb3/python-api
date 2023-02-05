import uvicorn
from fastapi import FastAPI, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
# 导入子路由
from routers import stock_router,stockfilter_router,bttest
import os


tags_metadata = [
    {
        # name 要对应 tags 参数值
        "name": "stock",
        "description": "Operations with users. The **login** logic is also here.",
    }
]

# 主路由
app = FastAPI(
    
    title="Zen",
    description="基于Zen的python-API后台",
    version="0.0.1",
    terms_of_service="http://example.com/terms/",
    tags_metadata=tags_metadata
)


origins = ["*"]
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# 添加子路由
app.include_router(stock_router)
app.include_router(stockfilter_router)
app.include_router(bttest)

app.mount('/public', StaticFiles(directory="tmphtml"), 'public')

@app.get("/")
async def root():
    return {"message": "Hello Bigger Applications!"}


if __name__ == "__main__":
    uvicorn.run(app="zen:app", host="127.0.0.1", debug=True, reload=True)
 