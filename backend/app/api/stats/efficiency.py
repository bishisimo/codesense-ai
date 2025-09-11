"""
开发效率统计API路由
"""
import arrow
from typing import Annotated, Optional
from datetime import datetime

from fastapi import APIRouter, Depends, Query
from sqlalchemy import select, func, and_, or_
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_session
from app.core.security import get_current_user
from app.models import MergeRequest, CodeReview
from app.schemas.statistics import EfficiencyMetrics

router = APIRouter()

# 依赖项
SessionDep = Annotated[AsyncSession, Depends(get_session)]
UserDep = Annotated[dict, Depends(get_current_user)]


def get_time_range(period: str, start_date: Optional[arrow.Arrow] = None, end_date: Optional[arrow.Arrow] = None):
    """根据时间周期获取时间范围（使用Arrow UTC时间）"""
    now = arrow.utcnow()
    
    if period == "today":
        start = now.floor('day')
        end = now
    elif period == "this_week":
        start = now.floor('week')
        end = now
    elif period == "this_month":
        start = now.floor('month')
        end = now
    elif period == "week":
        start = now.shift(days=-7)
        end = now
    elif period == "month":
        start = now.shift(days=-30)
        end = now
    elif period == "quarter":
        start = now.shift(days=-90)
        end = now
    elif period == "year":
        start = now.shift(days=-365)
        end = now
    else:  # custom
        start = start_date or now.shift(days=-30)
        end = end_date or now
    
    return start, end


def get_mr_time_conditions(start_date: datetime, end_date: datetime, time_criteria: str = "created"):
    """根据时间判断标准构建MR查询条件"""
    if time_criteria == "created":
        return [
            MergeRequest.mr_created_at >= start_date,
            MergeRequest.mr_created_at <= end_date
        ]
    elif time_criteria == "updated":
        return [
            MergeRequest.mr_updated_at >= start_date,
            MergeRequest.mr_updated_at <= end_date
        ]
    elif time_criteria == "activity":
        return [
            or_(
                and_(
                    MergeRequest.mr_created_at >= start_date,
                    MergeRequest.mr_created_at <= end_date
                ),
                and_(
                    MergeRequest.mr_updated_at >= start_date,
                    MergeRequest.mr_updated_at <= end_date
                )
            )
        ]
    else:
        return [
            MergeRequest.mr_created_at >= start_date,
            MergeRequest.mr_created_at <= end_date
        ]


@router.get("/", summary="获取开发效率指标")
async def get_efficiency_metrics(
    session: SessionDep,
    current_user: UserDep,
    period: str = "this_month",
    project_ids: Optional[str] = None,
    authors: Optional[str] = None,
    time_criteria: str = "activity"
):
    """获取开发效率指标"""
    
    # 获取时间范围
    start_arrow, end_arrow = get_time_range(period)
    start_date = start_arrow.datetime
    end_date = end_arrow.datetime
    
    # 构建基础查询条件
    base_conditions = get_mr_time_conditions(start_date, end_date, time_criteria)
    
    # 解析项目ID筛选
    if project_ids:
        try:
            project_id_list = [int(x.strip()) for x in project_ids.split(",")]
            base_conditions.append(MergeRequest.project_id.in_(project_id_list))
        except ValueError:
            pass
    
    # 解析作者筛选
    if authors:
        author_list = [x.strip() for x in authors.split(",")]
        base_conditions.append(MergeRequest.author.in_(author_list))
    
    # 计算时间跨度（天数）
    period_days = (end_date - start_date).days
    if period_days == 0:
        period_days = 1
    
    # 平均MR处理时间（从创建到合并的时间）- 使用简单的天数计算
    avg_mr_duration_query = select(
        func.avg(
            func.datediff(MergeRequest.mr_updated_at, MergeRequest.mr_created_at) * 24
        )
    ).where(
        and_(
            MergeRequest.state == 'merged',
            *base_conditions
        )
    )
    avg_mr_duration = await session.scalar(avg_mr_duration_query) or 0
    
    # 平均审查时间（从审查开始到完成的时间）- 使用简单的天数计算
    avg_review_time_query = select(
        func.avg(
            func.datediff(CodeReview.updated_at, CodeReview.created_at) * 24
        )
    ).select_from(
        CodeReview.__table__.join(MergeRequest.__table__, CodeReview.merge_request_id == MergeRequest.id)
    ).where(
        and_(
            CodeReview.status == 'completed',
            CodeReview.score > 0,  # 只统计得分大于0的审查
            *base_conditions
        )
    )
    avg_review_time = await session.scalar(avg_review_time_query) or 0
    
    # 每日MR数量
    total_mrs = await session.scalar(
        select(func.count(MergeRequest.id)).where(and_(*base_conditions))
    ) or 0
    mrs_per_day = round(total_mrs / period_days, 2)
    
    # 每日提交数
    total_commits = await session.scalar(
        select(func.sum(MergeRequest.commits_count)).where(and_(*base_conditions))
    ) or 0
    commits_per_day = round(total_commits / period_days, 2)
    
    return EfficiencyMetrics(
        avg_mr_duration=round(avg_mr_duration, 2),
        avg_review_time=round(avg_review_time, 2),
        mrs_per_day=mrs_per_day,
        commits_per_day=commits_per_day
    )
