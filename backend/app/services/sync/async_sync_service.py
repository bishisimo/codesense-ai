"""
异步同步服务
将同步操作包装为后台任务，避免API超时
"""
import asyncio
from datetime import datetime
from typing import Dict, Any, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.services.sync.service import SyncService
from app.services.task import TaskManager, TaskResult
from app.core.database import get_session
from app.core.logging import get_logger

logger = get_logger("async_sync_service")


class AsyncSyncService:
    """异步同步服务"""
    
    def __init__(self):
        self.sync_service = SyncService()
        self.task_manager = TaskManager()
        self._register_handlers()
    
    def _register_handlers(self):
        """注册任务处理器"""
        self.task_manager.register_handler("sync_all", self._handle_sync_all)
        self.task_manager.register_handler("sync_project", self._handle_sync_project)
        self.task_manager.register_handler("sync_repositories", self._handle_sync_repositories)
        self.task_manager.register_handler("sync_merge_request", self._handle_sync_merge_request)
    
    async def submit_sync_all_task(self) -> str:
        """提交全量同步任务"""
        return await self.task_manager.submit_task("sync_all")
    
    async def submit_sync_project_task(self, project_id: int) -> str:
        """提交单个项目同步任务"""
        return await self.task_manager.submit_task("sync_project", project_id=project_id)
    
    async def submit_sync_repositories_task(self) -> str:
        """提交本地仓库同步任务"""
        return await self.task_manager.submit_task("sync_repositories")
    
    async def submit_sync_merge_request_task(self, mr_id: int) -> str:
        """提交单个合并请求同步任务"""
        return await self.task_manager.submit_task("sync_merge_request", mr_id=mr_id)
    
    def get_task_status(self, task_id: str) -> Optional[TaskResult]:
        """获取任务状态"""
        return self.task_manager.get_task_status(task_id)
    
    def cancel_task(self, task_id: str) -> bool:
        """取消任务"""
        return self.task_manager.cancel_task(task_id)
    
    # ==================== 任务处理器 ====================
    
    async def _handle_sync_all(self, task_result: TaskResult, **kwargs) -> Dict[str, Any]:
        """处理全量同步任务"""
        try:
            task_result.update_progress(0.1, "开始全量同步...")
            
            # 创建数据库会话
            async for session in get_session():
                try:
                    task_result.update_progress(0.2, "正在同步项目...")
                    
                    # 执行同步
                    result = await self.sync_service.sync_all_data(session)
                    
                    if result["success"]:
                        task_result.update_progress(1.0, "全量同步完成")
                        return {
                            "success": True,
                            "message": result["message"],
                            "strategy": result.get("strategy", "unknown"),
                            "details": {
                                "projects": result["projects"],
                                "merge_requests": result["merge_requests"]
                            }
                        }
                    else:
                        raise Exception(result["message"])
                        
                except Exception as e:
                    logger.error(f"全量同步任务失败: {e}")
                    raise e
                finally:
                    await session.close()
                    
        except Exception as e:
            logger.error(f"全量同步任务执行失败: {e}")
            raise e
    
    async def _handle_sync_project(self, task_result: TaskResult, project_id: int, **kwargs) -> Dict[str, Any]:
        """处理单个项目同步任务"""
        try:
            task_result.update_progress(0.1, f"开始同步项目 {project_id}...")
            
            # 创建数据库会话
            async for session in get_session():
                try:
                    task_result.update_progress(0.3, "正在获取项目信息...")
                    
                    # 执行同步
                    result = await self.sync_service.sync_single_project_incremental(session, project_id)
                    
                    if result["success"]:
                        task_result.update_progress(1.0, f"项目 {result['project_name']} 同步完成")
                        return {
                            "success": True,
                            "message": result["message"],
                            "data": {
                                "project_id": result["project_id"],
                                "project_name": result["project_name"],
                                "synced": result["synced"],
                                "updated": result["updated"],
                                "total": result["total"]
                            }
                        }
                    else:
                        raise Exception(result["message"])
                        
                except Exception as e:
                    logger.error(f"项目同步任务失败: {e}")
                    raise e
                finally:
                    await session.close()
                    
        except Exception as e:
            logger.error(f"项目同步任务执行失败: {e}")
            raise e
    
    async def _handle_sync_repositories(self, task_result: TaskResult, **kwargs) -> Dict[str, Any]:
        """处理本地仓库同步任务"""
        try:
            task_result.update_progress(0.1, "开始同步本地仓库...")
            
            # 创建数据库会话
            async for session in get_session():
                try:
                    task_result.update_progress(0.3, "正在扫描本地仓库...")
                    
                    # 暂时返回成功，实际实现需要根据具体需求
                    # TODO: 实现本地仓库同步逻辑
                    task_result.update_progress(1.0, "本地仓库同步完成")
                    return {
                        "success": True,
                        "message": "本地仓库同步完成（功能待实现）",
                        "data": {
                            "repositories": [],
                            "total": 0
                        }
                    }
                        
                except Exception as e:
                    logger.error(f"本地仓库同步任务失败: {e}")
                    raise e
                finally:
                    await session.close()
                    
        except Exception as e:
            logger.error(f"本地仓库同步任务执行失败: {e}")
            raise e
    
    async def _handle_sync_merge_request(self, task_result: TaskResult, mr_id: int, **kwargs) -> Dict[str, Any]:
        """处理单个合并请求同步任务"""
        try:
            task_result.update_progress(0.1, f"开始同步合并请求 {mr_id}...")
            
            # 创建数据库会话
            async for session in get_session():
                try:
                    task_result.update_progress(0.3, "正在获取合并请求信息...")
                    
                    # 获取MR记录
                    from app.models import MergeRequest, Project
                    
                    result = await session.execute(
                        select(MergeRequest).where(MergeRequest.id == mr_id)
                    )
                    mr = result.scalar_one_or_none()
                    
                    if not mr:
                        raise Exception(f"合并请求 {mr_id} 不存在")
                    
                    # 获取项目信息
                    project_result = await session.execute(
                        select(Project).where(Project.id == mr.project_id)
                    )
                    project = project_result.scalar_one_or_none()
                    
                    if not project:
                        raise Exception(f"项目 {mr.project_id} 不存在")
                    
                    task_result.update_progress(0.5, "正在从GitLab获取最新数据...")
                    
                    # 执行单个MR同步
                    sync_result = await self.sync_service.sync_single_merge_request(session, project, mr)
                    
                    if sync_result["success"]:
                        task_result.update_progress(1.0, f"合并请求 {mr_id} 同步完成")
                        return {
                            "success": True,
                            "message": f"合并请求 {mr_id} 同步完成",
                            "data": {
                                "mr_id": mr_id,
                                "synced": True,
                                "details": sync_result.get("details", {})
                            }
                        }
                    else:
                        raise Exception(sync_result.get("message", "同步失败"))
                        
                except Exception as e:
                    logger.error(f"合并请求同步任务失败: {e}")
                    raise e
                finally:
                    await session.close()
                    
        except Exception as e:
            logger.error(f"合并请求同步任务执行失败: {e}")
            raise e


# 全局异步同步服务实例
async_sync_service = AsyncSyncService()
