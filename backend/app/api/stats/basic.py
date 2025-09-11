"""
基础统计API路由 - 项目数量、MR数量等基础指标
"""
from typing import Annotated
from datetime import datetime

from fastapi import APIRouter, Depends
from sqlalchemy import select, func, and_
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_session
from app.core.security import get_current_user
from app.models import Project, MergeRequest, CodeReview

router = APIRouter()

# 依赖项
SessionDep = Annotated[AsyncSession, Depends(get_session)]
UserDep = Annotated[dict, Depends(get_current_user)]


@router.get("/summary", summary="获取基础统计汇总")
async def get_basic_summary(
    session: SessionDep,
    current_user: UserDep
):
    """获取基础统计汇总信息"""
    # 项目统计
    total_projects = await session.scalar(select(func.count(Project.id))) or 0
    
    # MR统计
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
    
    # 统计今日审查数量
    start_of_today = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
    today_reviews = await session.scalar(
        select(func.count(CodeReview.id))
        .where(
            CodeReview.status == "completed",
            CodeReview.created_at >= start_of_today
        )
    ) or 0
    
    # 计算审查覆盖率
    review_coverage = round(reviewed_mrs / total_mrs * 100, 2) if total_mrs > 0 else 0
    
    return {
        "total_projects": total_projects,
        "total_merge_requests": total_mrs,
        "reviewed_merge_requests": reviewed_mrs,
        "pending_merge_requests": pending_mrs,
        "opened_merge_requests": opened_mrs,
        "today_reviews": today_reviews,
        "review_coverage": review_coverage
    }
