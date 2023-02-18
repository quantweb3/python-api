import uvicorn,os
from fastapi import FastAPI, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
# 导入子路由
from routers import stock,stockfilter,bttest,chan 

tags_metadata = [{"name":"stock","description":"ZenFramework"}]

 
app = FastAPI(
    title="Zen",
    description="基于Zen的python-API后台",
    version="0.0.1",
    terms_of_service="http://example.com/terms/",
    tags_metadata=tags_metadata
)


origins = ["*"]
app.add_middleware(CORSMiddleware,allow_origins=origins,allow_credentials=True,allow_methods=["*"],allow_headers=["*"],)


# 添加子路由
app.include_router(stock)
app.include_router(stockfilter)
app.include_router(bttest)
app.include_router(chan)

## 静态文件
app.mount('/public', StaticFiles(directory="tmphtml"), 'public')

@app.get("/")
async def root():
    return {"message": "Hello Zen"}



if __name__ == "__main__":
    uvicorn.run(app="zen:app", host="127.0.0.1", debug=True, reload=True)
 