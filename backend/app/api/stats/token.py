"""
Token统计API路由
"""
from typing import Annotated, Optional
from datetime import datetime

from fastapi import APIRouter, Depends, Query
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_session
from app.core.security import get_current_user
from app.models import TokenUsage, AIModel, CodeReview, MergeRequest, Project
from app.schemas.statistics import TokenUsageTrend, TokenUsageByModel, TokenUsageByProject

router = APIRouter()

# 依赖项
SessionDep = Annotated[AsyncSession, Depends(get_session)]
UserDep = Annotated[dict, Depends(get_current_user)]


@router.get("/trends", summary="获取Token使用趋势")
async def get_token_usage_trends(
    session: SessionDep,
    current_user: UserDep,
    days: int = 30
):
    """获取Token使用趋势数据"""
    if days > 30:
        days = 30
    
    # 计算时间范围
    from datetime import timedelta
    end_date = datetime.now()
    start_date = end_date - timedelta(days=days-1)
    start_date = start_date.replace(hour=0, minute=0, second=0, microsecond=0)
    
    # 按天统计token使用
    token_trend_query = select(
        func.date(TokenUsage.created_at).label('date'),
        func.sum(TokenUsage.total_tokens).label('total_tokens'),
        func.sum(TokenUsage.direct_tokens).label('direct_tokens'),
        func.sum(TokenUsage.cache_tokens).label('cache_tokens'),
        func.sum(TokenUsage.prompt_tokens).label('prompt_tokens'),
        func.sum(TokenUsage.completion_tokens).label('completion_tokens'),
        func.sum(TokenUsage.cost).label('cost')
    ).where(
        TokenUsage.created_at >= start_date,
        TokenUsage.created_at <= end_date
    ).group_by(func.date(TokenUsage.created_at)).order_by('date')
    
    token_trend_result = await session.execute(token_trend_query)
    trends = []
    for row in token_trend_result:
        trends.append(TokenUsageTrend(
            date=row.date.strftime('%Y-%m-%d'),
            total_tokens=row.total_tokens or 0,
            direct_tokens=row.direct_tokens or 0,
            cache_tokens=row.cache_tokens or 0,
            prompt_tokens=row.prompt_tokens or 0,
            completion_tokens=row.completion_tokens or 0,
            cost=float(row.cost or 0)
        ))
    
    return trends


@router.get("/by-model", summary="按模型统计Token使用")
async def get_token_usage_by_model(
    session: SessionDep,
    current_user: UserDep,
    days: int = 30
):
    """按模型统计Token使用情况"""
    # 计算时间范围
    from datetime import timedelta
    end_date = datetime.now()
    start_date = end_date - timedelta(days=days-1)
    start_date = start_date.replace(hour=0, minute=0, second=0, microsecond=0)
    
    # 按模型统计Token使用
    token_by_model_query = select(
        AIModel.model_name,
        func.sum(TokenUsage.total_tokens).label('total_tokens'),
        func.sum(TokenUsage.direct_tokens).label('direct_tokens'),
        func.sum(TokenUsage.cache_tokens).label('cache_tokens'),
        func.sum(TokenUsage.cost).label('cost'),
        func.count(TokenUsage.id).label('usage_count')
    ).select_from(
        TokenUsage.__table__.join(AIModel.__table__, TokenUsage.model_id == AIModel.id)
    ).where(
        TokenUsage.created_at >= start_date,
        TokenUsage.created_at <= end_date
    ).group_by(AIModel.model_name).order_by(func.sum(TokenUsage.total_tokens).desc())
    
    token_by_model_result = await session.execute(token_by_model_query)
    models = []
    for row in token_by_model_result:
        models.append(TokenUsageByModel(
            model_name=row.model_name,
            total_tokens=row.total_tokens or 0,
            direct_tokens=row.direct_tokens or 0,
            cache_tokens=row.cache_tokens or 0,
            cost=float(row.cost or 0),
            usage_count=row.usage_count or 0
        ))
    
    return models


@router.get("/by-project", summary="按项目统计Token使用")
async def get_token_usage_by_project(
    session: SessionDep,
    current_user: UserDep,
    days: int = 30
):
    """按项目统计Token使用情况"""
    # 计算时间范围
    from datetime import timedelta
    end_date = datetime.now()
    start_date = end_date - timedelta(days=days-1)
    start_date = start_date.replace(hour=0, minute=0, second=0, microsecond=0)
    
    # 按项目统计Token使用
    token_by_project_query = select(
        Project.name.label('project_name'),
        func.sum(TokenUsage.total_tokens).label('total_tokens'),
        func.sum(TokenUsage.direct_tokens).label('direct_tokens'),
        func.sum(TokenUsage.cache_tokens).label('cache_tokens'),
        func.sum(TokenUsage.cost).label('cost'),
        func.count(func.distinct(TokenUsage.review_id)).label('review_count')
    ).select_from(
        TokenUsage.__table__.join(CodeReview.__table__, TokenUsage.review_id == CodeReview.id)
        .join(MergeRequest.__table__, CodeReview.merge_request_id == MergeRequest.id)
        .join(Project.__table__, MergeRequest.project_id == Project.id)
    ).where(
        TokenUsage.created_at >= start_date,
        TokenUsage.created_at <= end_date
    ).group_by(Project.name).order_by(func.sum(TokenUsage.total_tokens).desc())
    
    token_by_project_result = await session.execute(token_by_project_query)
    projects = []
    for row in token_by_project_result:
        projects.append(TokenUsageByProject(
            project_name=row.project_name,
            total_tokens=row.total_tokens or 0,
            direct_tokens=row.direct_tokens or 0,
            cache_tokens=row.cache_tokens or 0,
            cost=float(row.cost or 0),
            review_count=row.review_count or 0
        ))
    
    return projects


@router.get("/summary", summary="获取Token使用汇总")
async def get_token_summary(
    session: SessionDep,
    current_user: UserDep,
    days: int = 30
):
    """获取Token使用汇总信息"""
    # 计算时间范围
    from datetime import timedelta
    end_date = datetime.now()
    start_date = end_date - timedelta(days=days-1)
    start_date = start_date.replace(hour=0, minute=0, second=0, microsecond=0)
    
    # 统计总token使用量
    total_tokens = await session.scalar(
        select(func.sum(TokenUsage.total_tokens))
        .where(
            TokenUsage.total_tokens.isnot(None),
            TokenUsage.created_at >= start_date,
            TokenUsage.created_at <= end_date
        )
    ) or 0
    
    # 统计非缓存token使用量
    total_direct_tokens = await session.scalar(
        select(func.sum(TokenUsage.direct_tokens))
        .where(
            TokenUsage.direct_tokens.isnot(None),
            TokenUsage.created_at >= start_date,
            TokenUsage.created_at <= end_date
        )
    ) or 0
    
    # 统计缓存token使用量
    total_cache_tokens = await session.scalar(
        select(func.sum(TokenUsage.cache_tokens))
        .where(
            TokenUsage.cache_tokens.isnot(None),
            TokenUsage.created_at >= start_date,
            TokenUsage.created_at <= end_date
        )
    ) or 0
    
    # 统计总成本
    total_cost = await session.scalar(
        select(func.sum(TokenUsage.cost))
        .where(
            TokenUsage.cost.isnot(None),
            TokenUsage.created_at >= start_date,
            TokenUsage.created_at <= end_date
        )
    ) or 0
    
    return {
        "total_tokens": total_tokens,
        "total_direct_tokens": total_direct_tokens,
        "total_cache_tokens": total_cache_tokens,
        "total_cost": float(total_cost),
        "period_days": days
    }
