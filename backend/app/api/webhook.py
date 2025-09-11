"""
GitLab Webhook处理API路由
"""
import hashlib
import hmac
from typing import Any, Dict, Optional
from datetime import datetime

from fastapi import APIRouter, Request, HTTPException, status, Header
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.core.config import settings
from app.core.database import AsyncSessionLocal
from app.models import Project, MergeRequest
from app.services.sync import SyncService
from app.core.logging import get_logger

logger = get_logger("webhook")

router = APIRouter()


def verify_webhook_token(token: str, secret: str) -> bool:
    """验证GitLab webhook token"""
    if not secret:
        return True  # 如果没有配置密钥，跳过验证
    
    # GitLab使用简单的字符串比较，不是HMAC签名
    return hmac.compare_digest(token, secret)


@router.post("/gitlab", summary="GitLab Webhook处理")
async def handle_gitlab_webhook(
    request: Request,
    x_gitlab_event: str = Header(..., alias="X-Gitlab-Event"),
    x_gitlab_token: str = Header(None, alias="X-Gitlab-Token"),
):
    """处理GitLab发送的Webhook事件"""
    
    logger.info(f"收到GitLab webhook事件: {x_gitlab_event}")
    
    # 验证token
    if settings.GITLAB_WEBHOOK_SECRET:
        if not x_gitlab_token or not verify_webhook_token(
            x_gitlab_token, settings.GITLAB_WEBHOOK_SECRET
        ):
            logger.warning(f"Webhook token验证失败: {x_gitlab_token}")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid webhook token"
            )
    
    # 解析JSON数据
    try:
        data = await request.json()
    except Exception as e:
        logger.error(f"解析webhook JSON失败: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid JSON: {str(e)}"
        )
    
    # 根据事件类型处理
    async with AsyncSessionLocal() as session:
        try:
            result = await process_webhook_event(session, x_gitlab_event, data)
            await session.commit()
            logger.info(f"Webhook事件处理成功: {x_gitlab_event}")
            return result
            
        except Exception as e:
            await session.rollback()
            logger.error(f"Webhook处理失败: {str(e)}", exc_info=True)
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Error processing webhook: {str(e)}"
            )


async def process_webhook_event(session: AsyncSession, event_type: str, data: Dict[str, Any]) -> Dict[str, Any]:
    """处理webhook事件"""
    
    if event_type == "Merge Request Hook":
        return await handle_merge_request_event(session, data)
    elif event_type == "Push Hook":
        return await handle_push_event(session, data)
    elif event_type == "Issue Hook":
        return await handle_issue_event(session, data)
    elif event_type == "Note Hook":
        return await handle_note_event(session, data)
    elif event_type == "Pipeline Hook":
        return await handle_pipeline_event(session, data)
    else:
        logger.warning(f"未处理的事件类型: {event_type}")
        return {"status": "ignored", "event": event_type, "message": "Event type not handled"}


async def handle_merge_request_event(session: AsyncSession, data: Dict[str, Any]) -> Dict[str, Any]:
    """处理合并请求事件"""
    mr_data = data.get("object_attributes", {})
    project_data = data.get("project", {})
    
    if not mr_data or not project_data:
        logger.warning("合并请求事件数据不完整")
        return {"status": "error", "message": "Incomplete merge request data"}
    
    # 确保项目存在
    project = await get_or_create_project(session, project_data)
    
    # 获取或创建合并请求
    mr = await get_or_create_merge_request(session, mr_data, project.id)
    
    # 处理具体的动作
    action = mr_data.get("action")
    logger.info(f"合并请求事件: {action} - {mr_data.get('title', 'Unknown')}")
    
    # 根据动作执行不同的处理
    if action in ["opened", "reopened", "updated"]:
        # 触发数据同步
        try:
            sync_service = SyncService()
            sync_result = await sync_service.sync_merge_request(session, mr.gitlab_id, project.gitlab_id)
            logger.info(f"合并请求同步完成: {sync_result}")
        except Exception as e:
            logger.error(f"合并请求同步失败: {str(e)}")
    
    return {
        "status": "success",
        "event": "Merge Request Hook",
        "action": action,
        "merge_request_id": mr.gitlab_id,
        "project_id": project.gitlab_id
    }


async def handle_push_event(session: AsyncSession, data: Dict[str, Any]) -> Dict[str, Any]:
    """处理推送事件"""
    project_data = data.get("project", {})
    
    if not project_data:
        logger.warning("推送事件数据不完整")
        return {"status": "error", "message": "Incomplete push data"}
    
    # 确保项目存在
    project = await get_or_create_project(session, project_data)
    
    # 记录推送事件
    ref = data.get("ref", "")
    commits_count = len(data.get("commits", []))
    logger.info(f"推送事件 - 项目: {project.name}, 分支: {ref}, 提交数: {commits_count}")
    
    # 如果是主分支推送，可以考虑触发项目同步
    if ref.endswith(project.default_branch):
        try:
            sync_service = SyncService()
            sync_result = await sync_service.sync_project(session, project.gitlab_id)
            logger.info(f"主分支推送，项目同步完成: {sync_result}")
        except Exception as e:
            logger.error(f"主分支推送同步失败: {str(e)}")
    
    return {
        "status": "success",
        "event": "Push Hook",
        "project_id": project.gitlab_id,
        "ref": ref,
        "commits_count": commits_count
    }


async def handle_issue_event(session: AsyncSession, data: Dict[str, Any]) -> Dict[str, Any]:
    """处理Issue事件"""
    issue_data = data.get("object_attributes", {})
    project_data = data.get("project", {})
    
    if not issue_data or not project_data:
        logger.warning("Issue事件数据不完整")
        return {"status": "error", "message": "Incomplete issue data"}
    
    # 确保项目存在
    project = await get_or_create_project(session, project_data)
    
    action = issue_data.get("action")
    issue_title = issue_data.get("title", "Unknown")
    logger.info(f"Issue事件: {action} - {issue_title}")
    
    return {
        "status": "success",
        "event": "Issue Hook",
        "action": action,
        "issue_id": issue_data.get("iid"),
        "project_id": project.gitlab_id
    }


async def handle_note_event(session: AsyncSession, data: Dict[str, Any]) -> Dict[str, Any]:
    """处理评论事件"""
    note_data = data.get("object_attributes", {})
    project_data = data.get("project", {})
    
    if not note_data or not project_data:
        logger.warning("评论事件数据不完整")
        return {"status": "error", "message": "Incomplete note data"}
    
    # 确保项目存在
    project = await get_or_create_project(session, project_data)
    
    noteable_type = note_data.get("noteable_type", "Unknown")
    logger.info(f"评论事件 - 类型: {noteable_type}, 项目: {project.name}")
    
    return {
        "status": "success",
        "event": "Note Hook",
        "noteable_type": noteable_type,
        "project_id": project.gitlab_id
    }


async def handle_pipeline_event(session: AsyncSession, data: Dict[str, Any]) -> Dict[str, Any]:
    """处理Pipeline事件"""
    pipeline_data = data.get("object_attributes", {})
    project_data = data.get("project", {})
    
    if not pipeline_data or not project_data:
        logger.warning("Pipeline事件数据不完整")
        return {"status": "error", "message": "Incomplete pipeline data"}
    
    # 确保项目存在
    project = await get_or_create_project(session, project_data)
    
    status = pipeline_data.get("status", "Unknown")
    ref = pipeline_data.get("ref", "Unknown")
    logger.info(f"Pipeline事件 - 状态: {status}, 分支: {ref}, 项目: {project.name}")
    
    return {
        "status": "success",
        "event": "Pipeline Hook",
        "pipeline_status": status,
        "ref": ref,
        "project_id": project.gitlab_id
    }


async def get_or_create_project(session: AsyncSession, project_data: Dict[str, Any]) -> Project:
    """获取或创建项目"""
    gitlab_id = project_data.get("id")
    
    if not gitlab_id:
        raise ValueError("项目ID不能为空")
    
    # 查找现有项目
    result = await session.execute(
        select(Project).where(Project.gitlab_id == gitlab_id)
    )
    project = result.scalar_one_or_none()
    
    if not project:
        # 创建新项目
        project = Project(
            gitlab_id=gitlab_id,
            name=project_data.get("name", ""),
            namespace=project_data.get("namespace", ""),
            web_url=project_data.get("web_url", ""),
            default_branch=project_data.get("default_branch", "main"),
        )
        session.add(project)
        await session.flush()  # 获取ID
        logger.info(f"创建新项目: {project.name} (ID: {gitlab_id})")
    else:
        # 更新项目信息
        project.name = project_data.get("name", project.name)
        project.namespace = project_data.get("namespace", project.namespace)
        project.web_url = project_data.get("web_url", project.web_url)
        project.default_branch = project_data.get("default_branch", project.default_branch)
        logger.debug(f"更新项目信息: {project.name}")
    
    return project


async def get_or_create_merge_request(
    session: AsyncSession, 
    mr_data: Dict[str, Any], 
    project_id: int
) -> MergeRequest:
    """获取或创建合并请求"""
    gitlab_id = mr_data.get("iid")  # 注意：这里使用iid而不是id
    
    if not gitlab_id:
        raise ValueError("合并请求ID不能为空")
    
    # 查找现有合并请求
    result = await session.execute(
        select(MergeRequest).where(
            MergeRequest.gitlab_id == gitlab_id,
            MergeRequest.project_id == project_id
        )
    )
    mr = result.scalar_one_or_none()
    
    if not mr:
        # 创建新合并请求
        mr = MergeRequest(
            gitlab_id=gitlab_id,
            project_id=project_id,
            title=mr_data.get("title", ""),
            description=mr_data.get("description", ""),
            author=mr_data.get("author", {}).get("username", ""),
            source_branch=mr_data.get("source_branch", ""),
            target_branch=mr_data.get("target_branch", ""),
            state=mr_data.get("state", ""),
            created_at=mr_data.get("created_at"),
            updated_at=mr_data.get("updated_at"),
        )
        session.add(mr)
        await session.flush()
        logger.info(f"创建新合并请求: {mr.title} (ID: {gitlab_id})")
    else:
        # 更新合并请求信息
        mr.title = mr_data.get("title", mr.title)
        mr.description = mr_data.get("description", mr.description)
        mr.state = mr_data.get("state", mr.state)
        mr.updated_at = mr_data.get("updated_at", mr.updated_at)
        logger.debug(f"更新合并请求: {mr.title}")
    
    return mr


@router.get("/test", summary="测试Webhook连接")
async def test_webhook():
    """测试webhook连接"""
    return {
        "status": "ok",
        "message": "Webhook endpoint is working",
        "timestamp": datetime.utcnow().isoformat()
    }