"""
Loguru日志配置
提供结构化日志记录、文件轮转、异步日志等功能
"""
import sys
import os
from pathlib import Path
from typing import Dict, Any
from loguru import logger
from app.core.config import settings

# 日志格式配置
LOG_FORMAT = (
    "<green>{time:YYYY-MM-DD HH:mm:ss.SSS}</green> | "
    "<level>{level: <8}</level> | "
    "<cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> | "
    "<level>{message}</level>"
)

# 结构化日志格式（JSON格式，用于生产环境）
JSON_LOG_FORMAT = (
    '{{"time": "{time:YYYY-MM-DD HH:mm:ss.SSS}", '
    '"level": "{level}", '
    '"name": "{name}", '
    '"function": "{function}", '
    '"line": {line}, '
    '"message": "{message}", '
    '"extra": {extra}}}'
)

def setup_logging():
    """设置日志配置 - 使用默认控制台输出，只配置格式和级别"""
    
    # 移除默认处理器并重新添加自定义格式的控制台输出
    logger.remove()
    logger.add(
        sys.stdout,
        format=LOG_FORMAT,
        level="DEBUG" if settings.DEBUG else "INFO",
        colorize=True,
        backtrace=True,
        diagnose=True,
        enqueue=True,  # 异步日志
    )

def get_logger(name: str = None):
    """获取logger实例"""
    return logger.bind(name=name)

# 自定义日志上下文管理器
class LogContext:
    """日志上下文管理器，用于添加上下文信息"""
    
    def __init__(self, **kwargs):
        self.context = kwargs
    
    def __enter__(self):
        logger.bind(**self.context)
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        if exc_type:
            logger.exception(f"Context: {self.context}, Error: {exc_val}")
        return False

# 性能监控装饰器
def log_performance(func_name: str = None):
    """性能监控装饰器"""
    def decorator(func):
        import time
        from functools import wraps
        
        @wraps(func)
        async def async_wrapper(*args, **kwargs):
            start_time = time.time()
            try:
                result = await func(*args, **kwargs)
                execution_time = time.time() - start_time
                logger.info(
                    f"Function {func_name or func.__name__} completed in {execution_time:.3f}s",
                    extra={"execution_time": execution_time, "function": func.__name__}
                )
                return result
            except Exception as e:
                execution_time = time.time() - start_time
                logger.error(
                    f"Function {func_name or func.__name__} failed after {execution_time:.3f}s: {e}",
                    extra={"execution_time": execution_time, "function": func.__name__, "error": str(e)}
                )
                raise
        
        @wraps(func)
        def sync_wrapper(*args, **kwargs):
            start_time = time.time()
            try:
                result = func(*args, **kwargs)
                execution_time = time.time() - start_time
                logger.info(
                    f"Function {func_name or func.__name__} completed in {execution_time:.3f}s",
                    extra={"execution_time": execution_time, "function": func.__name__}
                )
                return result
            except Exception as e:
                execution_time = time.time() - start_time
                logger.error(
                    f"Function {func_name or func.__name__} failed after {execution_time:.3f}s: {e}",
                    extra={"execution_time": execution_time, "function": func.__name__, "error": str(e)}
                )
                raise
        
        # 根据函数类型返回相应的包装器
        import asyncio
        if asyncio.iscoroutinefunction(func):
            return async_wrapper
        else:
            return sync_wrapper
    
    return decorator

# 数据库操作日志装饰器
def log_db_operation(operation: str):
    """数据库操作日志装饰器"""
    def decorator(func):
        from functools import wraps
        
        @wraps(func)
        async def wrapper(*args, **kwargs):
            try:
                result = await func(*args, **kwargs)
                logger.info(
                    f"Database {operation} completed successfully",
                    extra={"db_operation": operation, "function": func.__name__}
                )
                return result
            except Exception as e:
                logger.error(
                    f"Database {operation} failed: {e}",
                    extra={"db_operation": operation, "function": func.__name__, "error": str(e)}
                )
                raise
        
        return wrapper
    return decorator

# API请求日志装饰器
def log_api_request(endpoint: str):
    """API请求日志装饰器"""
    def decorator(func):
        from functools import wraps
        
        @wraps(func)
        async def wrapper(*args, **kwargs):
            import time
            start_time = time.time()
            
            try:
                result = await func(*args, **kwargs)
                execution_time = time.time() - start_time
                
                logger.info(
                    f"API {endpoint} completed in {execution_time:.3f}s",
                    extra={
                        "api_endpoint": endpoint,
                        "execution_time": execution_time,
                        "status": "success"
                    }
                )
                return result
            except Exception as e:
                execution_time = time.time() - start_time
                logger.error(
                    f"API {endpoint} failed after {execution_time:.3f}s: {e}",
                    extra={
                        "api_endpoint": endpoint,
                        "execution_time": execution_time,
                        "status": "error",
                        "error": str(e)
                    }
                )
                raise
        
        return wrapper
    return decorator
