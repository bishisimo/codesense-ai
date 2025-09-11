"""
合并请求管理API路由
"""
from typing import Annotated, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import select, func, and_
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.database import get_session
from app.core.security import get_current_user
from app.models import MergeRequest, Project, CodeReview
from app.schemas.merge_request import MergeRequestListResponse, MergeRequestListItem

router = APIRouter()

# 依赖项
SessionDep = Annotated[AsyncSession, Depends(get_session)]
UserDep = Annotated[dict, Depends(get_current_user)]


@router.get("", response_model=MergeRequestListResponse, summary="获取合并请求列表")
async def get_merge_requests(
    session: SessionDep,
    current_user: UserDep,
    page: int = Query(1, ge=1, description="页码"),
    size: int = Query(10, ge=1, le=100, description="每页数量"),
    project_id: Optional[int] = Query(None, description="项目ID筛选"),
    title: Optional[str] = Query(None, description="标题筛选"),
    author: Optional[str] = Query(None, description="作者筛选"),
    state: Optional[str] = Query(None, description="状态筛选"),
    sort_by: str = Query("created_at", description="排序字段"),
    sort_order: str = Query("desc", description="排序方向")
):
    """获取合并请求列表，支持分页、筛选和排序"""
    
    # 构建查询
    query = select(MergeRequest).join(Project).options(
        selectinload(MergeRequest.project),
        selectinload(MergeRequest.code_reviews)
    )
    
    # 添加筛选条件
    filters = []
    if project_id:
        filters.append(Project.id == project_id)
    if title:
        filters.append(MergeRequest.title.ilike(f"%{title}%"))
    if author:
        filters.append(MergeRequest.author.ilike(f"%{author}%"))
    if state:
        filters.append(MergeRequest.state == state)
    
    if filters:
        query = query.where(and_(*filters))
    
    # 添加排序
    sort_column = getattr(MergeRequest, sort_by, MergeRequest.mr_created_at)
    if sort_order.lower() == "desc":
        query = query.order_by(sort_column.desc())
    else:
        query = query.order_by(sort_column.asc())
    
    # 计算总数
    count_query = select(func.count(MergeRequest.id)).join(Project)
    
    # 添加相同的筛选条件到计数查询
    if project_id:
        count_query = count_query.where(Project.id == project_id)
    if title:
        count_query = count_query.where(MergeRequest.title.ilike(f"%{title}%"))
    if author:
        count_query = count_query.where(MergeRequest.author.ilike(f"%{author}%"))
    if state:
        count_query = count_query.where(MergeRequest.state == state)
    
    total = await session.scalar(count_query) or 0
    
    # 分页
    offset = (page - 1) * size
    query = query.offset(offset).limit(size)
    
    # 执行查询
    result = await session.execute(query)
    merge_requests = result.scalars().all()
    
    # 转换为响应模型
    items = []
    for mr in merge_requests:
        # 获取最新审查
        latest_review = None
        if mr.code_reviews:
            latest_review = max(mr.code_reviews, key=lambda r: r.updated_at)
        
        # 确定审查状态
        review_status = "未审查"
        review_score = None
        review_id = None
        is_reviewed = 0
        is_latest_reviewed = 0
        is_reviewing = 0
        is_failed = 0 # 初始化失败状态
        
        # 检查是否有审查中的记录
        pending_review = await session.scalar(
            select(CodeReview).where(
                CodeReview.merge_request_id == mr.id,
                CodeReview.status == "pending"
            )
        )
        
        if pending_review:
            is_reviewing = 1
            review_status = "审查中"
            review_id = pending_review.id
        elif latest_review and latest_review.status == "completed":
            is_reviewed = 1
            review_score = latest_review.score
            review_id = latest_review.id
            
            # 检查是否为最新commit的审查
            if latest_review.commit_sha == mr.last_commit_sha:
                is_latest_reviewed = 1
                review_status = "已审查"
            else:
                review_status = "需要重新审查"
        elif latest_review and latest_review.status == "failed":
            review_status = "审查失败"
            review_id = latest_review.id
            is_failed = 1 # 设置失败状态
        
        items.append(MergeRequestListItem(
            id=mr.id,
            gitlab_id=mr.gitlab_id,
            title=mr.title,
            author=mr.author,
            source_branch=mr.source_branch,
            target_branch=mr.target_branch,
            state=mr.state,
            mr_created_at=mr.mr_created_at,
            mr_updated_at=mr.mr_updated_at,
            commits_count=mr.commits_count,
            changes_count=mr.changes_count,
            additions_count=mr.additions_count,
            deletions_count=mr.deletions_count,
            project_name=mr.project.name if mr.project else "",
            project_web_url=mr.project.web_url if mr.project else "",
            review_status=review_status,
            review_score=review_score,
            review_id=review_id,
            is_reviewed=is_reviewed,
            is_latest_reviewed=is_latest_reviewed,
            is_reviewing=is_reviewing,
            is_failed=is_failed,  # 添加失败状态字段
            last_commit_sha=mr.last_commit_sha,
            commit_id=mr.last_commit_sha[:8] if mr.last_commit_sha else None  # 添加简短的commit ID
        ))
    
    return MergeRequestListResponse(
        items=items,
        total=total,
        page=page,
        size=size,
        pages=(total + size - 1) // size
    )


@router.get("/{mr_id}/status", summary="获取单个合并请求状态")
async def get_merge_request_status(
    mr_id: int,
    session: SessionDep,
    current_user: UserDep
):
    """获取单个合并请求的详细状态信息"""
    try:
        # 查询指定的合并请求，使用eager loading加载相关数据
        result = await session.execute(
            select(MergeRequest)
            .join(Project)
            .where(MergeRequest.id == mr_id)
            .options(selectinload(MergeRequest.code_reviews))
        )
        mr = result.scalar_one_or_none()
        
        if not mr:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"合并请求 {mr_id} 不存在"
            )
        
        # 获取最新审查
        latest_review = None
        if mr.code_reviews:
            latest_review = max(mr.code_reviews, key=lambda r: r.updated_at)
        
        # 确定审查状态
        review_status = "未审查"
        review_score = None
        review_id = None
        is_reviewed = 0
        is_latest_reviewed = 0
        is_reviewing = 0
        is_failed = 0
        
        # 检查是否有审查中的记录
        pending_review = await session.scalar(
            select(CodeReview).where(
                CodeReview.merge_request_id == mr.id,
                CodeReview.status == "pending"
            )
        )
        
        if pending_review:
            is_reviewing = 1
            review_status = "审查中"
            review_id = pending_review.id
        elif latest_review and latest_review.status == "completed":
            is_reviewed = 1
            review_score = latest_review.score
            review_id = latest_review.id
            
            # 检查是否为最新commit的审查
            if latest_review.commit_sha == mr.last_commit_sha:
                is_latest_reviewed = 1
                review_status = "已审查"
            else:
                review_status = "需要重新审查"
        elif latest_review and latest_review.status == "failed":
            review_status = "审查失败"
            review_id = latest_review.id
            is_failed = 1
        
        return {
            "id": mr.id,
            "gitlab_id": mr.gitlab_id,
            "title": mr.title,
            "state": mr.state,
            "review_status": review_status,
            "review_score": review_score,
            "review_id": review_id,
            "is_reviewed": is_reviewed,
            "is_latest_reviewed": is_latest_reviewed,
            "is_reviewing": is_reviewing,
            "is_failed": is_failed,
            "last_commit_sha": mr.last_commit_sha,
            "updated_at": mr.updated_at.isoformat() if mr.updated_at else None,
            "mr_updated_at": mr.mr_updated_at.isoformat() if mr.mr_updated_at else None
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"获取合并请求状态失败: {str(e)}"
        )


@router.get("/needing-review", summary="获取需要审查的合并请求")
async def get_merge_requests_needing_review(
    session: SessionDep,
    current_user: UserDep
):
    """获取需要审查的合并请求列表"""
    # 查询打开状态且没有已完成审查的合并请求
    query = select(MergeRequest).join(Project).where(
        MergeRequest.state == "opened",
        ~MergeRequest.id.in_(
            select(MergeRequest.id)
            .join(CodeReview)
            .where(CodeReview.status == "completed")
        )
    ).order_by(MergeRequest.mr_created_at.desc())
    
    result = await session.execute(query)
    mrs = result.scalars().all()
    
    return [
        {
            "id": mr.id,
            "title": mr.title,
            "author": mr.author,
            "project_name": mr.project.name if mr.project else "",
            "created_at": mr.mr_created_at,
            "web_url": mr.project.web_url if mr.project else ""
        }
        for mr in mrs
    ]
