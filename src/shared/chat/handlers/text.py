from typing import Dict, Any
from .base import BaseMessageHandler
from ..session import Message
from ...ai.factory import AIModelFactory, ModelType
from ...utils.logger import logger

class TextMessageHandler(BaseMessageHandler):
    """文本消息處理器"""
    
    def __init__(self):
        super().__init__()
        self.supported_types = ["text"]
    
    async def validate(self, message: Message) -> bool:
        """驗證文本消息"""
        return (
            message.type == "text" and
            isinstance(message.content, str) and
            len(message.content.strip()) > 0
        )
    
    async def preprocess(self, message: Message) -> Message:
        """預處理文本消息"""
        # 清理文本
        message.content = message.content.strip()
        return message
    
    async def handle(self, message: Message) -> Dict[str, Any]:
        """處理文本消息"""
        try:
            if not await self.validate(message):
                raise ValueError("無效的文本消息")
            
            # 預處理
            message = await self.preprocess(message)
            
            # 創建 AI 模型
            model = await AIModelFactory.create(ModelType.GEMINI)
            
            # 生成響應
            response = await model.generate(message.content)
            
            # 後處理響應
            result = {
                "success": True,
                "response": response.text,
                "model": response.model.value,
                "tokens": response.tokens
            }
            
            return await self.postprocess(result)
            
        except Exception as e:
            return await self.handle_error(e)
    
    async def postprocess(self, result: Dict[str, Any]) -> Dict[str, Any]:
        """後處理結果"""
        if result.get("success"):
            # 添加額外的處理邏輯，例如過濾敏感詞等
            result["processed"] = True
        return result 