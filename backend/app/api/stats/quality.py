"""
代码质量统计API路由
"""
import arrow
from typing import Annotated, Optional
from datetime import datetime

from fastapi import APIRouter, Depends, Query
from sqlalchemy import select, func, and_, or_, case
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_session
from app.core.security import get_current_user
from app.models import MergeRequest, CodeReview
from app.schemas.statistics import CodeQualityTrend, TechnicalDebt

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


@router.get("/trends", summary="获取代码质量趋势")
async def get_quality_trends(
    session: SessionDep,
    current_user: UserDep,
    period: str = "this_month",
    project_ids: Optional[str] = None,
    authors: Optional[str] = None,
    time_criteria: str = "activity"
):
    """获取代码质量趋势数据"""
    
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
    
    # 代码质量趋势查询
    quality_trends_query = select(
        func.date(CodeReview.created_at).label('date'),
        func.avg(CodeReview.score).label('avg_score'),
        func.count(CodeReview.id).label('review_count'),
        func.sum(
            case(
                (CodeReview.score >= 7, 1),
                else_=0
            )
        ).label('passed_reviews')
    ).select_from(
        CodeReview.__table__.join(MergeRequest.__table__, CodeReview.merge_request_id == MergeRequest.id)
    ).where(
        and_(
            CodeReview.status == "completed",
            CodeReview.score > 0,  # 只统计得分大于0的审查
            *base_conditions
        )
    ).group_by(func.date(CodeReview.created_at)).order_by('date')
    
    quality_trends_result = await session.execute(quality_trends_query)
    quality_trends = []
    
    for row in quality_trends_result:
        review_count = row.review_count or 0
        passed_reviews = row.passed_reviews or 0
        pass_rate = round(passed_reviews / review_count * 100, 2) if review_count > 0 else 0
        
        quality_trends.append(CodeQualityTrend(
            date=row.date.strftime('%Y-%m-%d'),
            avg_score=round(row.avg_score, 2) if row.avg_score else None,
            review_count=review_count,
            pass_rate=pass_rate
        ))
    
    return quality_trends


@router.get("/technical-debt", summary="获取技术债务统计")
async def get_technical_debt(
    session: SessionDep,
    current_user: UserDep,
    period: str = "this_month",
    project_ids: Optional[str] = None,
    authors: Optional[str] = None,
    time_criteria: str = "activity"
):
    """获取技术债务统计数据"""
    
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
    
    # 长期待处理MR数量（超过7天）
    long_pending_query = select(func.count(MergeRequest.id)).where(
        and_(
            MergeRequest.state == "opened",
            MergeRequest.mr_created_at <= datetime.now().replace(hour=0, minute=0, second=0, microsecond=0).replace(day=datetime.now().day - 7),
            *base_conditions
        )
    )
    long_pending = await session.scalar(long_pending_query) or 0
    
    # 重复审查MR数量（有多个审查记录的MR）
    re_reviewed_query = select(func.count(func.distinct(CodeReview.merge_request_id))).where(
        and_(
            CodeReview.merge_request_id.in_(
                select(CodeReview.merge_request_id)
                .group_by(CodeReview.merge_request_id)
                .having(func.count(CodeReview.id) > 1)
            ),
            *base_conditions
        )
    )
    re_reviewed = await session.scalar(re_reviewed_query) or 0
    
    # 最老待处理MR天数
    oldest_pending_query = select(
        func.datediff(datetime.now(), func.min(MergeRequest.mr_created_at))
    ).where(
        and_(
            MergeRequest.state == "opened",
            *base_conditions
        )
    )
    oldest_pending_days = await session.scalar(oldest_pending_query)
    
    return TechnicalDebt(
        long_pending_mrs=long_pending,
        re_reviewed_mrs=re_reviewed,
        high_risk_patterns=0,  # 暂时设为0，后续可以基于代码分析实现
        oldest_pending_days=int(oldest_pending_days) if oldest_pending_days else None
    )
