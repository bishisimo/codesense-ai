import httpx
from app.core.config import settings
from app.services.notification.notifier import NotifierInterface, NotificationMessage, logger

class FeishuNotifier(NotifierInterface):
    """飞书通知器"""

    def __init__(self):
        self.webhook_url = settings.NOTIFICATIONS_FEISHU_WEBHOOK_URL
        self.enabled = settings.NOTIFICATIONS_FEISHU_ENABLED

    async def send(self, message: NotificationMessage) -> bool:
        """发送飞书通知"""
        if not self.enabled or not self.webhook_url:
            return False

        try:
            # 构建飞书消息格式
            payload = {
                "msg_type": "interactive",
                "card": {
                    "elements": [
                        {
                            "tag": "div",
                            "text": {
                                "content": f"**{message.title}**\n\n{message.content}",
                                "tag": "lark_md"
                            }
                        }
                    ],
                    "header": {
                        "title": {
                            "content": "代码审查通知",
                            "tag": "plain_text"
                        }
                    }
                }
            }

            async with httpx.AsyncClient() as client:
                response = await client.post(
                    self.webhook_url,
                    json=payload,
                    timeout=10.0
                )
                response.raise_for_status()

            return True

        except Exception as e:
            logger.error(f"Failed to send Feishu notification: {str(e)}")
            return False
