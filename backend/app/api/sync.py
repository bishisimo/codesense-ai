"""
数据同步API路由 - 异步任务版本
"""
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.core.database import get_session
from app.core.security import get_current_user
from app.models import MergeRequest, Project
from app.services.sync import SyncService
from app.services.sync.async_sync_service import async_sync_service

router = APIRouter()

# 依赖项
SessionDep = Annotated[AsyncSession, Depends(get_session)]
UserDep = Annotated[dict, Depends(get_current_user)]


@router.get("/status", summary="获取同步状态")
async def get_sync_status(
        session: SessionDep,
        current_user: UserDep
):
    """获取同步状态"""
    try:
        sync_service = SyncService()
        strategy = await sync_service._determine_sync_strategy(session)
        return {
            "sync_strategy": strategy,
            "message": "同步状态查询成功"
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"获取同步状态失败: {str(e)}"
        )


@router.post("/", summary="同步GitLab数据")
async def sync_gitlab_data(
        current_user: UserDep
):
    """从GitLab API获取最新数据 - 异步任务模式，避免超时"""
    try:
        # 提交异步任务
        task_id = await async_sync_service.submit_sync_all_task()
        
        return {
            "success": True,
            "message": "同步任务已提交，正在后台执行",
            "task_id": task_id,
            "status": "submitted"
        }

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"提交同步任务失败: {str(e)}"
        )


@router.post("/projects/{project_id}", summary="同步指定项目")
async def sync_single_project(
        project_id: int,
        current_user: UserDep
):
    """同步指定项目的MR数据 - 异步任务模式"""
    try:
        # 提交异步任务
        task_id = await async_sync_service.submit_sync_project_task(project_id)
        
        return {
            "success": True,
            "message": f"项目 {project_id} 同步任务已提交，正在后台执行",
            "task_id": task_id,
            "project_id": project_id,
            "status": "submitted"
        }

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"提交项目同步任务失败: {str(e)}"
        )


@router.post("/repositories", summary="同步本地Git仓库")
async def sync_local_repositories(
        current_user: UserDep
):
    """同步本地Git仓库数据 - 异步任务模式"""
    try:
        # 提交异步任务
        task_id = await async_sync_service.submit_sync_repositories_task()
        
        return {
            "success": True,
            "message": "本地仓库同步任务已提交，正在后台执行",
            "task_id": task_id,
            "status": "submitted"
        }

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"提交本地仓库同步任务失败: {str(e)}"
        )


@router.post("/merge-requests/{mr_id}", summary="同步单个合并请求")
async def sync_single_merge_request(
        mr_id: int,
        session: SessionDep,
        current_user: UserDep
):
    """同步单个合并请求的最新数据 - 同步执行"""
    try:
        # 直接执行同步，不使用异步任务
        sync_service = SyncService()
        
        # 获取MR记录
        
        result = await session.execute(
            select(MergeRequest).where(MergeRequest.id == mr_id)
        )
        mr = result.scalar_one_or_none()
        
        if not mr:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"合并请求 {mr_id} 不存在"
            )
        
        # 获取项目信息
        project_result = await session.execute(
            select(Project).where(Project.id == mr.project_id)
        )
        project = project_result.scalar_one_or_none()
        
        if not project:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"项目 {mr.project_id} 不存在"
            )
        
        # 执行同步
        sync_result = await sync_service.sync_single_merge_request(session, project, mr)
        
        if sync_result["success"]:
            return {
                "success": True,
                "message": f"合并请求 {mr_id} 同步完成",
                "mr_id": mr_id,
                "status": "completed",
                "details": sync_result.get("details", {})
            }
        else:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=sync_result.get("message", "同步失败")
            )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"同步合并请求失败: {str(e)}"
        )


# ==================== 任务状态查询API ====================

@router.get("/tasks/{task_id}", summary="获取任务状态")
async def get_task_status(
        task_id: str,
        current_user: UserDep
):
    """获取异步任务的状态和进度"""
    try:
        task_result = async_sync_service.get_task_status(task_id)
        
        if not task_result:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="任务不存在"
            )
        
        return {
            "success": True,
            "task_id": task_id,
            "status": task_result.status.value,
            "progress": task_result.progress,
            "message": task_result.message,
            "started_at": task_result.started_at.isoformat() if task_result.started_at else None,
            "completed_at": task_result.completed_at.isoformat() if task_result.completed_at else None,
            "result": task_result.result,
            "error": task_result.error
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"获取任务状态失败: {str(e)}"
        )


@router.delete("/tasks/{task_id}", summary="取消任务")
async def cancel_task(
        task_id: str,
        current_user: UserDep
):
    """取消正在执行的任务"""
    try:
        success = async_sync_service.cancel_task(task_id)
        
        if not success:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="任务无法取消（可能已完成或不存在）"
            )
        
        return {
            "success": True,
            "message": "任务已取消",
            "task_id": task_id
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"取消任务失败: {str(e)}"
        )
