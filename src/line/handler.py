from typing import Dict, Optional
from fastapi import Request, APIRouter
from linebot.v3.webhook import WebhookHandler
from linebot.v3.messaging import MessagingApi
from linebot.v3.messaging.models import TextMessage
from linebot.models import TextSendMessage
from linebot.v3.webhooks.models.message_event import MessageEvent
from ..shared.config.config import settings
from ..shared.events.publisher import event_publisher
from ..shared.events.types import MessageEvent as AppMessageEvent
from ..shared.utils.logger import logger

class LineBotHandler:
    """LINE Bot 處理器"""
    
    def __init__(self):
        self.handler = WebhookHandler(settings.LINE_CHANNEL_SECRET)
        self._setup_handlers()
    
    def _setup_handlers(self):
        """設置事件處理器"""
        @self.handler.add(MessageEvent)
        async def handle_message(event):
            """處理消息事件"""
            return await self.handle_message(event)
    
    async def handle_message(self, event):
        """處理消息事件"""
        if isinstance(event.message, TextMessage):
            # 發布消息事件
            app_event = AppMessageEvent(
                message_id=event.message.id,
                user_id=event.source.user_id,
                content=event.message.text
            )
            await event_publisher.publish(app_event)
            return TextSendMessage(text=event.message.text)
        return None
    
    async def handle_request(
        self,
        request: Request,
        body: str,
        signature: str
    ):
        """處理 webhook 請求"""
        try:
            await self.handler.handle(body, signature)
            return True
        except Exception as e:
            logger.error(f"處理 webhook 請求失敗: {str(e)}")
            return False

# 創建全局 LINE Bot 處理器實例
line_handler = LineBotHandler()

router = APIRouter()

@router.post("/events")
async def handle_event(app_event: dict):
    """處理應用事件"""
    await event_publisher.publish(app_event) 