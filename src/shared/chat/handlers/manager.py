from typing import Dict, Type
from .base import BaseMessageHandler
from .text import TextMessageHandler
from .image import ImageMessageHandler
from ..session import Message
from ...utils.logger import logger

class MessageHandlerManager:
    """消息處理器管理器"""
    
    def __init__(self):
        self._handlers: Dict[str, BaseMessageHandler] = {}
        self._register_default_handlers()
    
    def _register_default_handlers(self):
        """註冊默認處理器"""
        self.register_handler("text", TextMessageHandler())
        self.register_handler("image", ImageMessageHandler())
    
    def register_handler(self, message_type: str, handler: BaseMessageHandler):
        """註冊消息處理器"""
        if not isinstance(handler, BaseMessageHandler):
            raise TypeError("處理器必須繼承 BaseMessageHandler")
        self._handlers[message_type] = handler
    
    async def handle_message(self, message: Message) -> Dict:
        """處理消息"""
        try:
            handler = self._handlers.get(message.type)
            if not handler:
                raise ValueError(f"未找到處理器: {message.type}")
            
            return await handler.handle(message)
            
        except Exception as e:
            logger.error(f"處理消息失敗: {str(e)}")
            return {
                "success": False,
                "error": str(e)
            } 