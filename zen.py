import uvicorn
from fastapi import FastAPI, Depends
from fastapi.middleware.cors import CORSMiddleware
# 导入子路由
from routers import user_router, item_router,stock_router,stockfilter_router
import os

# 主路由
app = FastAPI(
    # 声明全局依赖项
    # 如果每个 APIRouter 都会用到这个依赖项，那么应该声明为全局依赖项
    
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
# app.include_router(user_router)
# app.include_router(item_router)
app.include_router(stock_router)
app.include_router(stockfilter_router)


 


@app.get("/")
async def root():
    return {"message": "Hello Bigger Applications!"}


if __name__ == "__main__":
    uvicorn.run(app="zen:app", host="127.0.0.1", debug=True, reload=True)
 