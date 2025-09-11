"""
FastAPI应用主入口
"""
import asyncio
from contextlib import asynccontextmanager
from typing import AsyncGenerator

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from app.core.config import settings
from app.core.database import create_db_and_tables
from app.core.logging import setup_logging, get_logger
from app.api import (
    dashboard, merge_requests, reviews, sync, scheduler, auth, webhook, 
    prompt_templates, template_standard
)
from app.api.stats.router import stats_router
from scripts.templates.create_default_review_template import create_builtin_template

# 设置日志配置
setup_logging()
logger = get_logger("main")


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """应用生命周期管理"""
    logger.info("应用启动中...")
    try:
        # 启动时创建数据库表
        await create_db_and_tables()
        logger.info("数据库表创建完成")

        # 初始化AI模型数据
        try:
            from scripts.ai_models.init_ai_models import init_ai_models
            await init_ai_models()
            logger.info("AI模型数据初始化完成")
        except Exception as e:
            logger.error(f"AI模型数据初始化失败: {str(e)}")

        # 创建/更新默认模板
        try:
            # 创建默认模板
            await create_builtin_template()
            logger.info("默认模板创建/更新完成")
        except Exception as e:
            logger.error(f"默认模板创建/更新失败: {str(e)}")

        # 启动任务管理器清理调度器
        try:
            from app.services.task import task_manager
            asyncio.create_task(task_manager.start_cleanup_scheduler())
            logger.info("任务管理器清理调度器启动完成")
        except Exception as e:
            logger.error(f"任务管理器清理调度器启动失败: {str(e)}")

        logger.info("应用启动完成")
    except Exception as e:
        logger.error(f"应用启动失败: {e}")
        raise
    yield
    logger.info("应用关闭中...")


# 创建FastAPI应用
app = FastAPI(
    title="GitLab代码AI审查系统",
    description="基于AI的GitLab代码审查和管理系统",
    version="0.1.0",
    lifespan=lifespan,
)

# 配置CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 包含路由
app.include_router(auth.router, prefix="/api/auth", tags=["认证"])
app.include_router(dashboard.router, prefix="/api/dashboard", tags=["仪表板"])
app.include_router(merge_requests.router, prefix="/api/merge-requests", tags=["合并请求"])
app.include_router(reviews.router, prefix="/api/reviews", tags=["代码审查"])
app.include_router(sync.router, prefix="/api/sync", tags=["数据同步"])
app.include_router(scheduler.router, prefix="/api/scheduler", tags=["调度器"])
app.include_router(webhook.router, prefix="/api/webhook", tags=["Webhook"])
app.include_router(prompt_templates.router, prefix="/api/prompt-templates", tags=["Prompt模板"])
app.include_router(template_standard.router, prefix="/api/template", tags=["标准化模板"])

# 统计相关路由
app.include_router(stats_router, prefix="/api", tags=["数据统计"])

# 静态文件服务（前端）
try:
    app.mount("/", StaticFiles(directory="frontend/dist", html=True), name="static")
except RuntimeError:
    # 开发环境下前端可能还没构建
    pass


@app.get("/api/health")
async def health_check():
    """健康检查接口"""
    logger.debug("健康检查请求")
    return {"status": "healthy", "service": "code-reviewer"}


if __name__ == "__main__":
    import uvicorn
    
    uvicorn.run(
        "app.main:app",
        host=settings.SERVER_HOST,
        port=settings.SERVER_PORT,
        reload=settings.RELOAD,  # 使用配置中的热重载设置
    )
