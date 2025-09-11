"""
项目统计API路由
"""
import arrow
from typing import Annotated, Optional, List
from datetime import datetime

from fastapi import APIRouter, Depends, Query
from sqlalchemy import select, func, and_, or_, case
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_session
from app.core.security import get_current_user
from app.models import MergeRequest, Project, CodeReview
from app.schemas.statistics import ProjectStats

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


@router.get("/", summary="获取项目统计")
async def get_project_statistics(
    session: SessionDep,
    current_user: UserDep,
    period: str = "this_month",
    project_ids: Optional[str] = None,
    authors: Optional[str] = None,
    time_criteria: str = "activity"
):
    """获取项目统计数据"""
    
    # 获取时间范围
    start_arrow, end_arrow = get_time_range(period)
    start_date = start_arrow.datetime
    end_date = end_arrow.datetime
    
    # 构建基础查询条件
    base_conditions = get_mr_time_conditions(start_date, end_date, time_criteria)
    
    # 解析项目ID筛选
    project_id_list = None
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
    
    # 项目统计查询
    project_stats_query = select(
        Project.id.label('project_id'),
        Project.name.label('project_name'),
        func.count(MergeRequest.id).label('total_mrs'),
        func.sum(
            case(
                (MergeRequest.state == 'merged', 1),
                else_=0
            )
        ).label('merged_mrs'),
        func.sum(
            case(
                (MergeRequest.state == 'opened', 1),
                else_=0
            )
        ).label('open_mrs'),
        func.sum(MergeRequest.additions_count).label('total_additions'),
        func.sum(MergeRequest.deletions_count).label('total_deletions'),
        func.sum(MergeRequest.additions_count - MergeRequest.deletions_count).label('net_changes'),
        func.avg(MergeRequest.additions_count + MergeRequest.deletions_count).label('avg_mr_size'),
        func.count(func.distinct(CodeReview.id)).label('reviewed_count')
    ).select_from(
        Project.__table__.join(MergeRequest.__table__, Project.id == MergeRequest.project_id)
        .outerjoin(
            CodeReview.__table__, 
            and_(
                MergeRequest.id == CodeReview.merge_request_id,
                CodeReview.status == "completed",  # 只统计成功完成的审查
                CodeReview.score > 0  # 只统计得分大于0的审查
            )
        )
    ).where(
        and_(*base_conditions)
    ).group_by(Project.id, Project.name).order_by(func.sum(MergeRequest.additions_count).desc())
    
    project_stats_result = await session.execute(project_stats_query)
    project_stats = []
    
    for row in project_stats_result:
        total_mrs = row.total_mrs or 0
        reviewed_count = row.reviewed_count or 0
        review_coverage = round(reviewed_count / total_mrs * 100, 2) if total_mrs > 0 else 0
        
        total_additions = row.total_additions or 0
        total_deletions = row.total_deletions or 0
        net_changes = row.net_changes or 0
        
        # 计算代码增长率和减少率
        code_growth_rate = round(total_additions / total_mrs, 2) if total_mrs > 0 else 0
        code_reduction_rate = round(total_deletions / total_mrs, 2) if total_mrs > 0 else 0
        
        project_stats.append(ProjectStats(
            project_id=row.project_id,
            project_name=row.project_name,
            total_mrs=total_mrs,
            merged_mrs=row.merged_mrs or 0,
            open_mrs=row.open_mrs or 0,
            total_additions=total_additions,
            total_deletions=total_deletions,
            net_changes=net_changes,
            avg_mr_size=round(row.avg_mr_size or 0, 2),
            review_coverage=review_coverage,
            code_growth_rate=code_growth_rate,
            code_reduction_rate=code_reduction_rate,
            avg_additions_per_mr=round(total_additions / total_mrs, 2) if total_mrs > 0 else 0,
            avg_deletions_per_mr=round(total_deletions / total_mrs, 2) if total_mrs > 0 else 0
        ))
    
    return project_stats
