import asyncio
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

from app.core.config import settings
from app.services.notification.notifier import NotifierInterface, NotificationMessage, logger


class EmailNotifier(NotifierInterface):
    """邮件通知器"""

    def __init__(self):
        self.smtp_server = settings.NOTIFICATIONS_EMAIL_SMTP_SERVER
        self.smtp_port = settings.NOTIFICATIONS_EMAIL_SMTP_PORT
        self.username = settings.NOTIFICATIONS_EMAIL_USERNAME
        self.password = settings.NOTIFICATIONS_EMAIL_PASSWORD
        self.enabled = settings.NOTIFICATIONS_EMAIL_ENABLED

    async def send(self, message: NotificationMessage) -> bool:
        """发送邮件通知"""
        if not self.enabled or not self.smtp_server:
            return False

        try:
            # 在线程池中执行同步的SMTP操作
            loop = asyncio.get_event_loop()
            return await loop.run_in_executor(
                None, self._send_email_sync, message
            )
        except Exception as e:
            logger.error(f"Failed to send email: {str(e)}")
            return False

    def _send_email_sync(self, message: NotificationMessage) -> bool:
        """同步发送邮件"""
        try:
            msg = MIMEMultipart()
            msg['From'] = self.username
            msg['Subject'] = message.title

            # HTML内容
            html_content = f"""
            <html>
            <body>
                <h2>{message.title}</h2>
                <div style="white-space: pre-wrap;">{message.content}</div>
                <hr>
                <p><small>由代码审查系统自动发送</small></p>
            </body>
            </html>
            """

            msg.attach(MIMEText(html_content, 'html', 'utf-8'))

            # 连接SMTP服务器并发送
            with smtplib.SMTP(self.smtp_server, self.smtp_port) as server:
                server.starttls()
                server.login(self.username, self.password)

                for recipient in message.recipients:
                    msg['To'] = recipient
                    server.send_message(msg)
                    del msg['To']

            return True

        except Exception as e:
            logger.error(f"SMTP error: {str(e)}")
            return False