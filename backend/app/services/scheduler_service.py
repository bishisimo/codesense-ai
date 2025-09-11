"""
定时任务服务
用于自动执行GitLab数据同步
"""
import asyncio
from datetime import datetime, timedelta
from typing import Optional
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_session
from app.services.sync import SyncService
from app.core.logging import get_logger, log_performance

logger = get_logger("scheduler_service")


class SchedulerService:
    """定时任务服务"""
    
    def __init__(self):
        self.sync_service = SyncService()
        self.is_running = False  # 默认关闭自动同步
        self.sync_interval = 30 * 60  # 30分钟
        self.last_sync_time: Optional[datetime] = None
    
    @log_performance("start_scheduler")
    async def start_scheduler(self):
        """启动定时任务调度器"""
        if self.is_running:
            logger.warning("调度器已经在运行")
            return
        
        self.is_running = True
        logger.info("启动定时任务调度器")
        
        try:
            while self.is_running:
                await self._run_sync_task()
                await asyncio.sleep(self.sync_interval)
        except Exception as e:
            logger.error(f"调度器运行出错: {e}")
            self.is_running = False
        finally:
            logger.info("定时任务调度器已停止")
    
    async def stop_scheduler(self):
        """停止定时任务调度器"""
        self.is_running = False
        logger.info("正在停止定时任务调度器...")
    
    @log_performance("run_sync_task")
    async def _run_sync_task(self):
        """执行同步任务"""
        try:
            logger.info("开始执行定时同步任务")
            
            # 创建数据库会话
            async for session in get_session():
                try:
                    # 执行优化同步
                    result = await self.sync_service.sync_all_data(session)
                    
                    if result["success"]:
                        self.last_sync_time = datetime.utcnow()
                        logger.info(f"定时同步成功: {result['message']}")
                    else:
                        logger.error(f"定时同步失败: {result['message']}")
                        
                except Exception as e:
                    logger.error(f"定时同步任务执行失败: {e}")
                finally:
                    await session.close()
                    
        except Exception as e:
            logger.error(f"定时同步任务出错: {e}")
    
    @log_performance("run_manual_sync")
    async def run_manual_sync(self) -> dict:
        """手动执行同步任务"""
        try:
            logger.info("开始执行手动同步任务")
            
            async for session in get_session():
                try:
                    result = await self.sync_service.sync_all_data(session)
                    
                    if result["success"]:
                        self.last_sync_time = datetime.utcnow()
                        logger.info(f"手动同步成功: {result['message']}")
                    else:
                        logger.error(f"手动同步失败: {result['message']}")
                    
                    return result
                    
                except Exception as e:
                    logger.error(f"手动同步任务执行失败: {e}")
                    return {
                        "success": False,
                        "message": f"手动同步失败: {str(e)}"
                    }
                finally:
                    await session.close()
                    
        except Exception as e:
            logger.error(f"手动同步任务出错: {e}")
            return {
                "success": False,
                "message": f"手动同步出错: {str(e)}"
            }
    
    def get_scheduler_status(self) -> dict:
        """获取调度器状态"""
        return {
            "is_running": self.is_running,
            "sync_interval_seconds": self.sync_interval,
            "last_sync_time": self.last_sync_time.isoformat() if self.last_sync_time else None,
            "next_sync_time": (self.last_sync_time + timedelta(seconds=self.sync_interval)).isoformat() if self.last_sync_time else None
        }
    
    def set_sync_interval(self, interval_seconds: int):
        """设置同步间隔"""
        if interval_seconds < 60:  # 最少1分钟
            raise ValueError("同步间隔不能少于60秒")
        
        self.sync_interval = interval_seconds
        logger.info(f"同步间隔已设置为 {interval_seconds} 秒")


# 全局调度器实例 - 延迟初始化
_scheduler_instance = None

def get_scheduler() -> SchedulerService:
    """获取调度器实例 - 延迟初始化"""
    global _scheduler_instance
    if _scheduler_instance is None:
        _scheduler_instance = SchedulerService()
    return _scheduler_instance

# 为了向后兼容，保留scheduler变量，但改为属性访问
class SchedulerProxy:
    """调度器代理类，用于延迟初始化"""
    def __getattr__(self, name):
        return getattr(get_scheduler(), name)

scheduler = SchedulerProxy()


async def start_background_scheduler():
    """启动后台调度器"""
    asyncio.create_task(scheduler.start_scheduler())


async def stop_background_scheduler():
    """停止后台调度器"""
    await scheduler.stop_scheduler()
