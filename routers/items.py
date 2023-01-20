#!usr/bin/env python
# -*- coding:utf-8 _*-
"""
# author: 小菠萝测试笔记

# time: 2021/9/28 7:26 下午
# file: items.py
"""

from fastapi import APIRouter, Depends

item_router = APIRouter(
    # 这里配置的 tags、dependencies、responses 对这个模块的内的所有路径操作都生效
    # 路径前缀，该模块下所有路径操作的前缀
    prefix="/items",
    # 标签
    tags=["items"],
  
    # 响应
    responses={404: {"description": "items Not found"}}
)


@item_router.get('/item')
async def index():
    return {}


@item_router.get('/item/list')
async def list():
    return {}
 