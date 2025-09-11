"""
调度器管理API路由
"""
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_session
from app.core.security import get_current_user
from app.services.scheduler_service import scheduler

router = APIRouter()

# 依赖项
SessionDep = Annotated[AsyncSession, Depends(get_session)]
UserDep = Annotated[dict, Depends(get_current_user)]


@router.get("/status", summary="获取调度器状态")
async def get_scheduler_status(
    session: SessionDep,
    current_user: UserDep
):
    """获取调度器运行状态"""
    try:
        status_info = scheduler.get_status()
        return {
            "running": status_info["running"],
            "interval": status_info["interval"],
            "last_run": status_info["last_run"],
            "next_run": status_info["next_run"],
            "total_runs": status_info["total_runs"],
            "successful_runs": status_info["successful_runs"],
            "failed_runs": status_info["failed_runs"]
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"获取调度器状态失败: {str(e)}"
        )


@router.post("/start", summary="启动调度器")
async def start_scheduler(
    session: SessionDep,
    current_user: UserDep
):
    """启动自动同步调度器"""
    try:
        result = scheduler.start()
        if result["success"]:
            return {
                "success": True,
                "message": "调度器已启动",
                "interval": result["interval"]
            }
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=result["message"]
            )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"启动调度器失败: {str(e)}"
        )


@router.post("/stop", summary="停止调度器")
async def stop_scheduler(
    session: SessionDep,
    current_user: UserDep
):
    """停止自动同步调度器"""
    try:
        result = scheduler.stop()
        if result["success"]:
            return {
                "success": True,
                "message": "调度器已停止"
            }
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=result["message"]
            )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"停止调度器失败: {str(e)}"
        )


@router.post("/sync-now", summary="立即执行同步")
async def sync_now(
    session: SessionDep,
    current_user: UserDep
):
    """立即执行一次同步任务"""
    try:
        result = await scheduler.sync_now(session)
        if result["success"]:
            return {
                "success": True,
                "message": "同步任务已执行",
                "details": result.get("details", {})
            }
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=result["message"]
            )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"执行同步任务失败: {str(e)}"
        )


@router.put("/interval", summary="设置同步间隔")
async def set_sync_interval(
    interval_minutes: int,
    session: SessionDep,
    current_user: UserDep
):
    """设置自动同步的时间间隔（分钟）"""
    try:
        if interval_minutes < 1:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="同步间隔不能小于1分钟"
            )
        
        result = scheduler.set_interval(interval_minutes)
        if result["success"]:
            return {
                "success": True,
                "message": f"同步间隔已设置为{interval_minutes}分钟",
                "interval": interval_minutes
            }
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=result["message"]
            )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"设置同步间隔失败: {str(e)}"
        )
