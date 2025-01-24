from abc import ABC, abstractmethod
from typing import Any, Dict
from ..session import Message
from ...utils.logger import logger

class BaseMessageHandler(ABC):
    """消息處理器基礎類"""
    
    def __init__(self):
        self.supported_types = []
    
    @abstractmethod
    async def handle(self, message: Message) -> Dict[str, Any]:
        """處理消息"""
        pass
    
    @abstractmethod
    async def validate(self, message: Message) -> bool:
        """驗證消息"""
        pass
    
    async def preprocess(self, message: Message) -> Message:
        """預處理消息"""
        return message
    
    async def postprocess(self, result: Dict[str, Any]) -> Dict[str, Any]:
        """後處理結果"""
        return result
    
    async def handle_error(self, error: Exception) -> Dict[str, Any]:
        """處理錯誤"""
        logger.error(f"消息處理錯誤: {str(error)}")
        return {
            "success": False,
            "error": str(error)
        } 