"""
代码审查API路由
"""
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.database import get_session
from app.core.security import get_current_user
from app.models import CodeReview, MergeRequest, TokenUsage
from app.schemas.review import CodeReviewResponse, ReviewResult
from app.services.review import ReviewService
from app.services.task import task_manager, TaskStatus

router = APIRouter()

# 依赖项
SessionDep = Annotated[AsyncSession, Depends(get_session)]
UserDep = Annotated[dict, Depends(get_current_user)]


@router.post("/merge-requests/{mr_id}/trigger", summary="手动触发代码审查")
async def trigger_review(
    mr_id: int,
    session: SessionDep,
    current_user: UserDep,
    force: bool = Query(False, description="是否强制审查"),
    template_id: int = Query(None, description="审查模板ID"),
    custom_instructions: str = Query("", description="自定义审查说明")
):
    """手动触发指定合并请求的代码审查（异步任务）"""
    
    # 检查合并请求是否存在
    mr = await session.get(MergeRequest, mr_id)
    if not mr:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="合并请求不存在"
        )
    
    # 检查是否有正在审查中的记录
    pending_review = await session.scalar(
        select(CodeReview).where(
            CodeReview.merge_request_id == mr_id,
            CodeReview.status == "pending"
        )
    )
    
    # 如果有正在审查中的记录且没有force参数，则拒绝
    if pending_review and not force:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="该合并请求正在审查中，如需强制重新审查请使用force参数"
        )
    
    try:
        # 立即创建审查记录，状态为pending
        from app.services.review.service import ReviewService
        review_service = ReviewService()
        
        # 直接调用ReviewService创建审查记录
        review = await review_service.review_merge_request(
            session, mr, force_refresh=force, template_id=template_id, custom_instructions=custom_instructions
        )
        
        if review:
            return {
                "success": True,
                "message": "代码审查已启动，正在处理中...",
                "review_id": review.id,
                "status": "pending"
            }
        else:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="创建审查记录失败"
            )
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"启动代码审查失败: {str(e)}"
        )


@router.post("/merge-requests/{mr_id}/enhanced", response_model=ReviewResult, summary="触发增强代码审查")
async def trigger_enhanced_review(
    mr_id: int,
    session: SessionDep,
    current_user: UserDep,
    repo_path: str = Query(..., description="本地仓库路径"),
    force_refresh: bool = Query(False, description="是否强制刷新")
):
    """手动触发指定合并请求的增强代码审查，使用本地Git仓库进行详细分析"""
    
    # 检查合并请求是否存在
    mr = await session.get(MergeRequest, mr_id)
    if not mr:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="合并请求不存在"
        )
    
    try:
        # 使用增强审查服务进行审查
        review_service = ReviewService()
        review = await review_service.enhanced_review_merge_request(
            session, mr, repo_path, force_refresh=force_refresh
        )
        
        return ReviewResult(
            success=True,
            message="增强代码审查已完成",
            review_id=review.id if review else None
        )
        
    except Exception as e:
        return ReviewResult(
            success=False,
            message=f"增强代码审查失败: {str(e)}",
            review_id=None
        )


@router.post("/merge-requests/{mr_id}/review-with-template", response_model=ReviewResult, summary="使用指定模板进行代码审查")
async def trigger_review_with_template(
    mr_id: int,
    session: SessionDep,
    current_user: UserDep,
    template_name: str = Query(..., description="模板名称"),
    force_refresh: bool = Query(False, description="是否强制刷新")
):
    """使用指定的模板对合并请求进行代码审查"""
    
    # 检查合并请求是否存在
    mr = await session.get(MergeRequest, mr_id)
    if not mr:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="合并请求不存在"
        )
    
    try:
        # 使用指定模板进行审查
        review_service = ReviewService()
        review = await review_service.review_merge_request(
            session, mr, force_refresh=force_refresh, template_name=template_name
        )
        
        return ReviewResult(
            success=True,
            message=f"使用模板 '{template_name}' 的代码审查已启动",
            review_id=review.id if review else None
        )
        
    except Exception as e:
        return ReviewResult(
            success=False,
            message=f"代码审查失败: {str(e)}",
            review_id=None
        )


@router.get("/{review_id}", response_model=CodeReviewResponse, summary="获取代码审查详情")
async def get_review(
    review_id: int,
    session: SessionDep,
    current_user: UserDep
):
    """获取指定代码审查的详细信息"""
    
    review = await session.get(
        CodeReview, 
        review_id,
        options=[selectinload(CodeReview.comments)]
    )
    
    if not review:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="代码审查不存在"
        )
    
    return review


@router.get("/{review_id}/content", summary="获取审查内容")
async def get_review_content(
    review_id: int,
    session: SessionDep,
    current_user: UserDep
):
    """获取代码审查的详细内容（Markdown格式）"""
    
    review = await session.get(CodeReview, review_id)
    
    if not review:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="代码审查不存在"
        )
    
    return {
        "review_id": review.id,
        "content": review.review_content or "",
        "score": review.score,
        "status": review.status,
        "created_at": review.created_at,
        "updated_at": review.updated_at,
    }


@router.get("/merge-requests/{mr_id}/history", summary="获取合并请求的所有审查历史")
async def get_merge_request_reviews(
    mr_id: int,
    session: SessionDep,
    current_user: UserDep
):
    """获取指定合并请求的所有审查历史，按创建时间降序排列"""
    
    # 检查合并请求是否存在
    mr = await session.get(MergeRequest, mr_id)
    if not mr:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="合并请求不存在"
        )
    
    # 获取所有审查记录，按创建时间降序排列，过滤掉失败的审查报告
    reviews = await session.execute(
        select(CodeReview)
        .where(
            CodeReview.merge_request_id == mr_id,
            CodeReview.status != "failed"  # 过滤掉失败的审查报告
        )
        .order_by(CodeReview.created_at.desc())
        .options(selectinload(CodeReview.comments))
    )
    
    review_list = reviews.scalars().all()
    
    # 构建返回数据
    reviews = []
    for review in review_list:
        # 从TokenUsage表获取token信息
        token_usage = await session.scalar(
            select(TokenUsage)
            .where(TokenUsage.review_id == review.id)
            .limit(1)
        )
        
        tokens_used = token_usage.total_tokens if token_usage else None
        
        reviews.append({
            "id": review.id,
            "commit_sha": review.commit_sha,
            "commit_sha_short": review.commit_sha[:8] if review.commit_sha else "",
            "score": review.score,
            "status": review.status,
            "reviewer_type": review.reviewer_type,
            "tokens_used": tokens_used,
            "created_at": review.created_at.isoformat(),
            "updated_at": review.updated_at.isoformat(),
            "is_latest": review.commit_sha == mr.last_commit_sha,
            "comments_count": len(review.comments) if review.comments else 0,
            "is_reviewing": review.status == "pending"
        })
    
    return {
        "merge_request_id": mr_id,
        "merge_request_title": mr.title,
        "latest_commit_sha": mr.last_commit_sha,
        "reviews": reviews,
        "total": len(reviews)
    }


# 异步任务相关API端点
@router.get("/tasks/{task_id}/status", summary="查询代码审查任务状态")
async def get_review_task_status(
    task_id: str,
    current_user: UserDep
):
    """查询代码审查任务状态"""
    
    task_result = task_manager.get_task_status(task_id)
    if not task_result:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="任务不存在"
        )
    
    return task_result.to_dict()


@router.post("/tasks/{task_id}/cancel", summary="取消代码审查任务")
async def cancel_review_task(
    task_id: str,
    current_user: UserDep
):
    """取消代码审查任务"""
    
    success = task_manager.cancel_task(task_id)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="无法取消任务，任务可能已完成或不存在"
        )
    
    return {"message": "任务已取消"}


@router.get("/tasks/{task_id}/result", summary="获取代码审查结果")
async def get_review_task_result(
    task_id: str,
    current_user: UserDep
):
    """获取代码审查结果"""
    
    task_result = task_manager.get_task_status(task_id)
    if not task_result:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="任务不存在"
        )
    
    if task_result.status == TaskStatus.PENDING:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="任务尚未开始"
        )
    
    if task_result.status == TaskStatus.RUNNING:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="任务正在执行中"
        )
    
    if task_result.status == TaskStatus.FAILED:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"任务执行失败: {task_result.error}"
        )
    
    if task_result.status == TaskStatus.CANCELLED:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="任务已取消"
        )
    
    # 任务完成，返回结果
    result = task_result.result
    return ReviewResult(
        success=result.get("success", True),
        message=result.get("message", "代码审查已完成"),
        review_id=result.get("review_id")
    )
