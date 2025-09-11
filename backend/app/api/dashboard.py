"""
仪表板API路由 - 统计信息和概览
"""
from typing import Annotated
from datetime import datetime

from fastapi import APIRouter, Depends
from sqlalchemy import select, func, and_
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_session
from app.core.security import get_current_user
from app.models import Project, MergeRequest, CodeReview, TokenUsage

router = APIRouter()

# 依赖项
SessionDep = Annotated[AsyncSession, Depends(get_session)]
UserDep = Annotated[dict, Depends(get_current_user)]


@router.get("/stats", summary="获取统计信息")
async def get_stats(
    session: SessionDep,
    current_user: UserDep
):
    """获取系统统计信息"""
    total_projects = await session.scalar(select(func.count(Project.id))) or 0
    total_mrs = await session.scalar(select(func.count(MergeRequest.id))) or 0
    
    # 统计已审查的合并请求（有已完成审查的）
    reviewed_mrs = await session.scalar(
        select(func.count(MergeRequest.id.distinct()))
        .select_from(MergeRequest)
        .join(CodeReview)
        .where(
            and_(
                CodeReview.status == "completed",
                CodeReview.score > 0  # 只统计得分大于0的审查
            )
        )
    ) or 0
    
    # 统计待审查的合并请求（打开状态且没有已完成审查的）
    pending_mrs = await session.scalar(
        select(func.count(MergeRequest.id))
        .where(
            MergeRequest.state == "opened",
            ~MergeRequest.id.in_(
                select(MergeRequest.id)
                .join(CodeReview)
                .where(
            and_(
                CodeReview.status == "completed",
                CodeReview.score > 0  # 只统计得分大于0的审查
            )
        )
            )
        )
    ) or 0
    
    # 统计打开状态的合并请求总数
    opened_mrs = await session.scalar(
        select(func.count(MergeRequest.id))
        .where(MergeRequest.state == "opened")
    ) or 0
    
    # 统计AI模型token使用量
    total_tokens = await session.scalar(
        select(func.sum(TokenUsage.total_tokens))
        .where(TokenUsage.total_tokens.isnot(None))
    ) or 0
    
    # 统计非缓存token使用量
    total_direct_tokens = await session.scalar(
        select(func.sum(TokenUsage.direct_tokens))
        .where(TokenUsage.direct_tokens.isnot(None))
    ) or 0
    
    # 统计缓存token使用量
    total_cache_tokens = await session.scalar(
        select(func.sum(TokenUsage.cache_tokens))
        .where(TokenUsage.cache_tokens.isnot(None))
    ) or 0
    
    # 统计输入token使用量
    total_prompt_tokens = await session.scalar(
        select(func.sum(TokenUsage.prompt_tokens))
        .where(TokenUsage.prompt_tokens.isnot(None))
    ) or 0
    
    # 统计输出token使用量
    total_completion_tokens = await session.scalar(
        select(func.sum(TokenUsage.completion_tokens))
        .where(TokenUsage.completion_tokens.isnot(None))
    ) or 0
    
    # 统计本月token使用量
    start_of_month = datetime.now().replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    monthly_tokens = await session.scalar(
        select(func.sum(TokenUsage.total_tokens))
        .where(
            TokenUsage.total_tokens.isnot(None),
            TokenUsage.created_at >= start_of_month
        )
    ) or 0
    
    # 统计本月非缓存token使用量
    monthly_direct_tokens = await session.scalar(
        select(func.sum(TokenUsage.direct_tokens))
        .where(
            TokenUsage.direct_tokens.isnot(None),
            TokenUsage.created_at >= start_of_month
        )
    ) or 0
    
    # 统计本月缓存token使用量
    monthly_cache_tokens = await session.scalar(
        select(func.sum(TokenUsage.cache_tokens))
        .where(
            TokenUsage.cache_tokens.isnot(None),
            TokenUsage.created_at >= start_of_month
        )
    ) or 0
    
    # 统计本月输入token使用量
    monthly_prompt_tokens = await session.scalar(
        select(func.sum(TokenUsage.prompt_tokens))
        .where(
            TokenUsage.prompt_tokens.isnot(None),
            TokenUsage.created_at >= start_of_month
        )
    ) or 0
    
    # 统计本月输出token使用量
    monthly_completion_tokens = await session.scalar(
        select(func.sum(TokenUsage.completion_tokens))
        .where(
            TokenUsage.completion_tokens.isnot(None),
            TokenUsage.created_at >= start_of_month
        )
    ) or 0
    
    # 统计今日审查数量
    start_of_today = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
    today_reviews = await session.scalar(
        select(func.count(CodeReview.id))
        .where(
            CodeReview.status == "completed",
            CodeReview.created_at >= start_of_today
        )
    ) or 0
    
    return {
        "total_projects": total_projects,
        "total_merge_requests": total_mrs,
        "reviewed_merge_requests": reviewed_mrs,
        "pending_merge_requests": pending_mrs,
        "opened_merge_requests": opened_mrs,
        "total_tokens": total_tokens,
        "total_direct_tokens": total_direct_tokens,
        "total_cache_tokens": total_cache_tokens,
        "total_prompt_tokens": total_prompt_tokens,
        "total_completion_tokens": total_completion_tokens,
        "monthly_tokens": monthly_tokens,
        "monthly_direct_tokens": monthly_direct_tokens,
        "monthly_cache_tokens": monthly_cache_tokens,
        "monthly_prompt_tokens": monthly_prompt_tokens,
        "monthly_completion_tokens": monthly_completion_tokens,
        "today_reviews": today_reviews,
    }


@router.get("/projects", summary="获取项目列表")
async def get_projects(
    session: SessionDep,
    current_user: UserDep
):
    """获取所有项目列表"""
    projects = await session.execute(select(Project).order_by(Project.name))
    items = [{"id": p.id, "name": p.name, "gitlab_id": p.gitlab_id, "web_url": p.web_url} for p in projects.scalars().all()]
    return {"items": items}
