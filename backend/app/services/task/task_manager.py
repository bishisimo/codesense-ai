"""
AI任务管理器
处理长时间运行的AI生成任务
"""
import asyncio
import uuid
from datetime import datetime, timedelta
from typing import Dict, Any, Optional, Callable
from enum import Enum
import json
import logging

logger = logging.getLogger(__name__)


class TaskStatus(Enum):
    """任务状态"""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class TaskResult:
    """任务结果"""
    def __init__(self, task_id: str):
        self.task_id = task_id
        self.status = TaskStatus.PENDING
        self.result: Optional[Dict[str, Any]] = None
        self.error: Optional[str] = None
        self.created_at = datetime.utcnow()
        self.started_at: Optional[datetime] = None
        self.completed_at: Optional[datetime] = None
        self.progress: float = 0.0
        self.message: str = "任务等待中..."

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "task_id": self.task_id,
            "status": self.status.value,
            "result": self.result,
            "error": self.error,
            "created_at": self.created_at.isoformat(),
            "started_at": self.started_at.isoformat() if self.started_at else None,
            "completed_at": self.completed_at.isoformat() if self.completed_at else None,
            "progress": self.progress,
            "message": self.message
        }

    def update_progress(self, progress: float, message: str = None):
        """更新进度"""
        self.progress = max(0.0, min(1.0, progress))
        if message:
            self.message = message


class TaskManager:
    """任务管理器"""
    
    def __init__(self):
        self._tasks: Dict[str, TaskResult] = {}
        self._task_handlers: Dict[str, Callable] = {}
        self._cleanup_interval = 3600  # 1小时清理一次过期任务
        self._task_ttl = 86400  # 24小时任务过期时间
        
    def register_handler(self, task_type: str, handler: Callable):
        """注册任务处理器"""
        self._task_handlers[task_type] = handler
        
    async def submit_task(self, task_type: str, **kwargs) -> str:
        """提交任务"""
        task_id = str(uuid.uuid4())
        task_result = TaskResult(task_id)
        self._tasks[task_id] = task_result
        
        # 异步执行任务
        asyncio.create_task(self._execute_task(task_id, task_type, **kwargs))
        
        logger.info(f"任务已提交: {task_id}, 类型: {task_type}")
        return task_id
    
    async def _execute_task(self, task_id: str, task_type: str, **kwargs):
        """执行任务"""
        task_result = self._tasks.get(task_id)
        if not task_result:
            return
            
        try:
            task_result.status = TaskStatus.RUNNING
            task_result.started_at = datetime.utcnow()
            task_result.message = "任务执行中..."
            
            # 获取任务处理器
            handler = self._task_handlers.get(task_type)
            if not handler:
                raise ValueError(f"未找到任务处理器: {task_type}")
            
            # 执行任务
            result = await handler(task_result, **kwargs)
            
            # 任务完成
            task_result.status = TaskStatus.COMPLETED
            task_result.result = result
            task_result.completed_at = datetime.utcnow()
            task_result.progress = 1.0
            task_result.message = "任务完成"
            
            logger.info(f"任务完成: {task_id}")
            
        except Exception as e:
            # 任务失败
            task_result.status = TaskStatus.FAILED
            task_result.error = str(e)
            task_result.completed_at = datetime.utcnow()
            task_result.message = f"任务失败: {str(e)}"
            
            logger.error(f"任务失败: {task_id}, 错误: {str(e)}")
    
    def get_task_status(self, task_id: str) -> Optional[TaskResult]:
        """获取任务状态"""
        return self._tasks.get(task_id)
    
    def cancel_task(self, task_id: str) -> bool:
        """取消任务"""
        task_result = self._tasks.get(task_id)
        if task_result and task_result.status in [TaskStatus.PENDING, TaskStatus.RUNNING]:
            task_result.status = TaskStatus.CANCELLED
            task_result.completed_at = datetime.utcnow()
            task_result.message = "任务已取消"
            return True
        return False
    
    async def cleanup_expired_tasks(self):
        """清理过期任务"""
        now = datetime.utcnow()
        expired_tasks = []
        
        for task_id, task_result in self._tasks.items():
            if now - task_result.created_at > timedelta(seconds=self._task_ttl):
                expired_tasks.append(task_id)
        
        for task_id in expired_tasks:
            del self._tasks[task_id]
            
        if expired_tasks:
            logger.info(f"清理了 {len(expired_tasks)} 个过期任务")
    
    async def start_cleanup_scheduler(self):
        """启动清理调度器"""
        while True:
            await asyncio.sleep(self._cleanup_interval)
            await self.cleanup_expired_tasks()


# 全局任务管理器实例
task_manager = TaskManager()


# AI模板生成任务处理器
async def ai_template_generation_handler(task_result: TaskResult, **kwargs):
    """AI模板生成任务处理器"""
    from .template_generator import TemplateGeneratorService
    from .service import ai_service
    
    try:
        # 更新进度
        task_result.update_progress(0.1, "正在准备AI模型...")
        await asyncio.sleep(0.1)
        
        # 创建模板生成器实例
        template_generator = TemplateGeneratorService(ai_service)
        
        task_result.update_progress(0.3, "正在生成模板内容...")
        
        # 调用模板生成器
        result = await template_generator.generate_template(
            prompt=kwargs.get("prompt"),
            selected_variables=kwargs.get("selected_variables"),
            template_name=kwargs.get("template_name"),
            description=kwargs.get("description")
        )
        
        task_result.update_progress(0.8, "正在处理生成结果...")
        await asyncio.sleep(0.1)
        
        # 处理生成结果
        if result.get("success"):
            task_result.update_progress(1.0, "生成并验证成功")
        else:
            task_result.update_progress(1.0, "生成完成但验证失败")
        
        return result
        
    except Exception as e:
        logger.error(f"AI模板生成失败: {str(e)}")
        raise


# AI代码审查任务处理器
async def ai_code_review_handler(task_result: TaskResult, **kwargs):
    """AI代码审查任务处理器"""
    from app.services.review import ReviewService
    
    try:
        # 更新进度
        task_result.update_progress(0.1, "正在准备审查环境...")
        await asyncio.sleep(0.1)
        
        task_result.update_progress(0.2, "正在获取代码变更...")
        
        # 创建审查服务实例
        review_service = ReviewService()
        
        task_result.update_progress(0.4, "正在分析代码结构...")
        
        # 执行代码审查
        review = await review_service.review_merge_request(
            session=kwargs.get("session"),
            merge_request=kwargs.get("merge_request"),
            force_refresh=kwargs.get("force_refresh", False),
            template_name=kwargs.get("template_name")
        )
        
        task_result.update_progress(0.8, "正在生成审查报告...")
        await asyncio.sleep(0.1)
        
        task_result.update_progress(1.0, "审查完成")
        
        return {
            "review_id": review.id if review else None,
            "success": True,
            "message": "代码审查已完成"
        }
        
    except Exception as e:
        logger.error(f"AI代码审查失败: {str(e)}")
        raise


# 注册任务处理器
task_manager.register_handler("ai_template_generation", ai_template_generation_handler)
task_manager.register_handler("ai_code_review", ai_code_review_handler)
