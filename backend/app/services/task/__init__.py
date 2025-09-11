"""
任务服务模块

提供通用的任务管理功能，支持各种类型的异步任务：
- AI相关任务（模板生成、代码审查等）
- 数据同步任务
- 其他长时间运行的任务
"""
from .task_manager import TaskManager, TaskResult, TaskStatus, task_manager

__all__ = [
    "TaskManager",
    "TaskResult", 
    "TaskStatus",
    "task_manager"
]
