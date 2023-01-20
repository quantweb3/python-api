from fastapi import APIRouter, Depends, HTTPException

# 属于该模块的路由
user_router = APIRouter(
    # 这里配置的 tags、dependencies、responses 对这个模块的内的所有路径操作都生效
    # 路径前缀，该模块下所有路径操作的前缀
    prefix="/users",
    # 标签
    tags=["users"],
    # 响应
    responses={404: {"description": "users Not found"}}
)


@user_router.get('/account/login')
async def login():
    return {}


@user_router.get('/account/logout')
async def logout():
    return {}


# 单独给某个路径操作声明 tags、responses
@user_router.put(
    "/{item_id}",
    tags=["custom"],
    responses={403: {"description": "路径专属 Operation forbidden"}},
)
async def update_item(item_id: str):
    if item_id != "plumbus":
        raise HTTPException(
            status_code=403, detail="You can only update the item: plumbus"
        )
    return {"item_id": item_id, "name": "The great Plumbus"}
 