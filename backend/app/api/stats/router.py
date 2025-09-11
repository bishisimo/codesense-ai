"""
统计API统一路由入口

提供所有统计相关API的统一访问点
"""

from fastapi import APIRouter
from . import basic, token, project, user, quality, efficiency

# 创建统计API路由器
stats_router = APIRouter()

# 注册所有统计子路由
stats_router.include_router(
    basic.router, 
    prefix="/basic-stats", 
    tags=["基础统计"]
)

stats_router.include_router(
    token.router, 
    prefix="/token-stats", 
    tags=["Token统计"]
)

stats_router.include_router(
    project.router, 
    prefix="/project-stats", 
    tags=["项目统计"]
)

stats_router.include_router(
    user.router, 
    prefix="/user-stats", 
    tags=["用户统计"]
)

stats_router.include_router(
    quality.router, 
    prefix="/quality-stats", 
    tags=["质量统计"]
)

stats_router.include_router(
    efficiency.router, 
    prefix="/efficiency-stats", 
    tags=["效率统计"]
)
