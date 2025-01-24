from typing import Dict, Optional
from fastapi import Request
from linebot import WebhookHandler
from linebot.models import (
    MessageEvent,
    TextMessage,
    TextSendMessage
)
from ..shared.config.manager import config_manager
from ..shared.events.publisher import event_publisher
from ..shared.events.types import MessageEvent as AppMessageEvent
from ..shared.utils.logger import logger

class LineBotHandler:
    """LINE Bot 處理器"""
    
    def __init__(self):
        config = config_manager.get_line_config()
        self.handler = WebhookHandler(config.get("channel_secret"))
        self._setup_handlers()
    
    def _setup_handlers(self):
        """設置事件處理器"""
        # 處理文字消息
        @self.handler.add(MessageEvent, message=TextMessage)
        def handle_text_message(event):
            try:
                # 創建應用消息事件
                app_event = AppMessageEvent(
                    message_id=event.message.id,
                    user_id=event.source.user_id,
                    content=event.message.text
                )
                
                # 發布事件
                await event_publisher.publish(app_event)
                
                # 暫時回覆相同的消息
                return TextSendMessage(text=event.message.text)
                
            except Exception as e:
                logger.error(f"處理 LINE 消息失敗: {str(e)}")
                return TextSendMessage(text="抱歉，發生了錯誤。")
    
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