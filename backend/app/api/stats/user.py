"""
用户统计API路由
"""
import arrow
from typing import Annotated, Optional, List
from datetime import datetime

from fastapi import APIRouter, Depends, Query
from sqlalchemy import select, func, and_, or_, case
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_session
from app.core.security import get_current_user
from app.models import MergeRequest, CodeReview
from app.schemas.statistics import UserStats

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


def calculate_workdays(start_date: datetime, end_date: datetime):
    """计算工作日数量（周一到周五）"""
    start_arrow = arrow.get(start_date)
    end_arrow = arrow.get(end_date)
    workdays = 0
    
    current = start_arrow
    while current <= end_arrow:
        if current.weekday() < 5:  # 0-4 表示周一到周五
            workdays += 1
        current = current.shift(days=1)
    
    return workdays


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


@router.get("/", summary="获取用户统计")
async def get_user_statistics(
    session: SessionDep,
    current_user: UserDep,
    period: str = "this_month",
    project_ids: Optional[str] = None,
    authors: Optional[str] = None,
    time_criteria: str = "activity"
):
    """获取用户统计数据"""
    
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
    
    # 用户统计查询 - 修复JOIN导致的重复计算问题
    user_stats_query = select(
        MergeRequest.author,
        func.count(MergeRequest.id).label('total_mrs'),
        func.sum(
            case(
                (MergeRequest.state == 'merged', 1),
                else_=0
            )
        ).label('merged_mrs'),
        func.sum(MergeRequest.additions_count).label('total_additions'),
        func.sum(MergeRequest.deletions_count).label('total_deletions'),
        func.sum(MergeRequest.additions_count - MergeRequest.deletions_count).label('net_changes'),
        func.avg(MergeRequest.additions_count + MergeRequest.deletions_count).label('avg_mr_size'),
        func.sum(MergeRequest.commits_count).label('total_commits')
    ).where(
        and_(*base_conditions)
    ).group_by(MergeRequest.author).order_by(func.sum(MergeRequest.additions_count).desc())
    
    user_stats_result = await session.execute(user_stats_query)
    user_stats = []
    
    for row in user_stats_result:
        total_mrs = row.total_mrs or 0
        total_additions = row.total_additions or 0
        total_deletions = row.total_deletions or 0
        net_changes = row.net_changes or 0
        
        # 计算代码增长率和减少率
        code_growth_rate = round(total_additions / total_mrs, 2) if total_mrs > 0 else 0
        code_reduction_rate = round(total_deletions / total_mrs, 2) if total_mrs > 0 else 0
        
        # 获取该用户的平均审查评分（使用子查询避免JOIN重复计算）
        avg_review_score = None
        if total_mrs > 0:
            review_score_query = select(func.avg(CodeReview.score)).select_from(
                CodeReview.__table__.join(
                    MergeRequest.__table__,
                    CodeReview.merge_request_id == MergeRequest.id
                )
            ).where(
                and_(
                    MergeRequest.author == row.author,
                    CodeReview.status == "completed",
                    CodeReview.score > 0,
                    *base_conditions
                )
            )
            review_score_result = await session.execute(review_score_query)
            avg_review_score = review_score_result.scalar()
        
        # 计算生产力评分（使用新的分层结构算法）
        productivity_score = 0
        contribution_score = 0
        code_efficiency_score = 0
        quality_score = 0
        participation_score = 0
        
        if total_mrs > 0:
            import math
            
            # 计算工作日数量
            workdays = calculate_workdays(start_date, end_date)
            
            # 计算基础数据
            total_changes = total_additions + total_deletions
            avg_changes_per_mr = total_changes / total_mrs
            total_commits = row.total_commits or 0
            
            # 工作日标准化
            daily_contribution = total_changes / workdays if workdays > 0 else 0
            daily_commits = total_commits / workdays if workdays > 0 else 0
            daily_mrs = total_mrs / workdays if workdays > 0 else 0
            
            # 贡献层 (40%): 总变更量（工作日标准化）- 目标100分
            contribution_score = math.log(daily_contribution + 1) * 13
            
            # 代码效率层 (30%): 单次MR代码量（工作日标准化）- 目标100分
            code_efficiency_score = math.log(avg_changes_per_mr + 1) * 16
            
            # 质量层 (20%): 审查评分（直接使用）- 目标100分
            quality_score = float(avg_review_score or 60)
            
            # 参与活跃层 (10%): MR和commit数量（工作日标准化）- 目标100分
            participation_score = min(math.log(daily_mrs + 1) * 50, 50) + min(math.log(daily_commits + 1) * 15, 50)
            
            # 最终评分（先计算加权总分，再限制为100）
            productivity_score = (contribution_score * 0.4 + 
                                 code_efficiency_score * 0.3 + 
                                 quality_score * 0.20 + 
                                 participation_score * 0.1)
            productivity_score = min(100, productivity_score)
            productivity_score = round(productivity_score, 2)
        
        user_stats.append(UserStats(
            author=row.author,
            total_mrs=total_mrs,
            merged_mrs=row.merged_mrs or 0,
            total_additions=total_additions,
            total_deletions=total_deletions,
            net_changes=net_changes,
            avg_mr_size=round(row.avg_mr_size or 0, 2),
            avg_review_score=round(avg_review_score, 2) if avg_review_score else None,
            total_commits=row.total_commits or 0,
            code_growth_rate=code_growth_rate,
            code_reduction_rate=code_reduction_rate,
            avg_additions_per_mr=round(total_additions / total_mrs, 2) if total_mrs > 0 else 0,
            avg_deletions_per_mr=round(total_deletions / total_mrs, 2) if total_mrs > 0 else 0,
            # 分层生产力评分
            contribution_score=round(contribution_score, 2) if total_mrs > 0 else 0,
            code_efficiency_score=round(code_efficiency_score, 2) if total_mrs > 0 else 0,
            quality_score=round(quality_score, 2) if total_mrs > 0 else 0,
            participation_score=round(participation_score, 2) if total_mrs > 0 else 0,
            productivity_score=productivity_score
        ))
    
    return user_stats
