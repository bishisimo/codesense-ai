import asyncio
from typing import List
from app.core.config import settings
from app.services.notification.email import EmailNotifier
from app.services.notification.feishu import FeishuNotifier
from app.services.notification.notifier import NotificationMessage, logger


class NotificationService:
    """通知服务管理器"""

    def __init__(self):
        self.notifiers = []
        self._initialize_notifiers()

    def _initialize_notifiers(self):
        """初始化通知器"""
        # 邮件通知
        if settings.NOTIFICATIONS_EMAIL_ENABLED:
            self.notifiers.append(EmailNotifier())

        # 飞书通知
        if settings.NOTIFICATIONS_FEISHU_ENABLED:
            self.notifiers.append(FeishuNotifier())

    async def send_notification(self, message: NotificationMessage) -> List[bool]:
        """发送通知到所有启用的渠道"""
        if not self.notifiers:
            return []

        tasks = [notifier.send(message) for notifier in self.notifiers]
        results = await asyncio.gather(*tasks, return_exceptions=True)

        # 处理异常
        final_results = []
        for result in results:
            if isinstance(result, Exception):
                logger.error(f"Notification error: {str(result)}")
                final_results.append(False)
            else:
                final_results.append(result)

        return final_results

    async def send_review_notification(
            self,
            project_name: str,
            mr_title: str,
            author: str,
            score: int,
            review_content: str,
            recipients: List[str] = None
    ):
        """发送代码审查完成通知"""
        score_status = "优秀" if score >= 80 else "良好" if score >= 60 else "需改进"

        title = f"代码审查完成 - {project_name}"
        content = f"""
项目: {project_name}
合并请求: {mr_title}
作者: {author}
评分: {score} ({score_status})

审查详情:
{review_content}
"""

        message = NotificationMessage(
            title=title,
            content=content,
            recipients=recipients or []
        )

        return await self.send_notification(message)