from typing import List, Optional, Dict, Any, Callable, Type, Tuple
from fastapi import Request, HTTPException
from linebot.v3.webhook import WebhookParser
from linebot.v3.webhooks import (
    MessageEvent,
    TextMessageContent,
    ImageMessageContent,
    AudioMessageContent,
    Event
)
from ..config.config import config
from ..utils.logger import logger
from .client import line_client

class LineWebhookHandler:
    """LINE Webhook 處理器"""
    def __init__(self):
        self._handlers: Dict[Type[Event], Callable] = {}
    
    def add(self, event_type: Type[Event]) -> Callable:
        """註冊事件處理器"""
        def decorator(func: Callable) -> Callable:
            self._handlers[event_type] = func
            return func
        return decorator
    
    async def handle_request(self, request: Request) -> List[Any]:
        """處理 webhook 請求"""
        signature = request.headers.get('X-Line-Signature', '')
        body = await request.body()
        
        if not line_client.verify_webhook(body, signature):
            logger.error("無效的 webhook 簽名")
            raise Exception("無效的 webhook 簽名")
        
        events = line_client.parse_webhook_body(body)
        results = []
        
        for event in events:
            handler = self._handlers.get(type(event))
            if handler:
                try:
                    result = handler(event)
                    results.append(result)  # 無條件添加結果
                except Exception as e:
                    logger.error(f"處理事件時出錯: {str(e)}")
                    raise
        
        return results

class MessageHandler:
    """消息處理器"""
    def __init__(self):
        self._handlers: Dict[Tuple[Type[Event], Type], Callable] = {}
    
    def add(self, message_type: Type) -> Callable:
        """註冊消息處理器"""
        def decorator(func: Callable) -> Callable:
            self._handlers[(MessageEvent, message_type)] = func
            return func
        return decorator
    
    def handle_event(self, event: MessageEvent) -> Any:
        """處理消息事件"""
        handler = self._handlers.get((MessageEvent, type(event.message)))
        if handler:
            try:
                return handler(event)
            except Exception as e:
                logger.error(f"處理消息時出錯: {str(e)}")
                raise
        return None

# 創建全局 Webhook 處理器實例
webhook_handler = LineWebhookHandler()
message_handler = MessageHandler()

# 導出類
__all__ = ['LineWebhookHandler', 'MessageHandler'] 