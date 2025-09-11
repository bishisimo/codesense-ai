"""
通知服务
"""
from abc import ABC, abstractmethod
from typing import Dict, Any, List
from app.core.logging import get_logger

logger = get_logger("notifier")


class NotificationMessage:
    """通知消息模型"""
    
    def __init__(
        self,
        title: str,
        content: str,
        recipients: List[str] = None,
        extra_data: Dict[str, Any] = None
    ):
        self.title = title
        self.content = content
        self.recipients = recipients or []
        self.extra_data = extra_data or {}


class NotifierInterface(ABC):
    """通知器接口"""
    
    @abstractmethod
    async def send(self, message: NotificationMessage) -> bool:
        """发送通知"""
        pass
