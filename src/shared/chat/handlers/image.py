from typing import Dict, Any
import aiohttp
from .base import BaseMessageHandler
from ..session import Message
from ...ai.factory import AIModelFactory, ModelType
from ...utils.logger import logger

class ImageMessageHandler(BaseMessageHandler):
    """圖片消息處理器"""
    
    def __init__(self):
        super().__init__()
        self.supported_types = ["image"]
    
    async def validate(self, message: Message) -> bool:
        """驗證圖片消息"""
        return (
            message.type == "image" and
            message.media_url is not None
        )
    
    async def preprocess(self, message: Message) -> Message:
        """預處理圖片消息"""
        if message.media_url:
            try:
                async with aiohttp.ClientSession() as session:
                    async with session.get(message.media_url) as response:
                        if response.status == 200:
                            message.content = await response.read()
                        else:
                            raise ValueError(f"下載圖片失敗: HTTP {response.status}")
            except Exception as e:
                logger.error(f"下載圖片失敗: {str(e)}")
                raise
        return message
    
    async def handle(self, message: Message) -> Dict[str, Any]:
        """處理圖片消息"""
        try:
            if not await self.validate(message):
                raise ValueError("無效的圖片消息")
            
            # 預處理
            message = await self.preprocess(message)
            
            # 創建 AI 模型
            model = await AIModelFactory.create(ModelType.GEMINI)
            
            # 分析圖片
            response = await model.analyze_image(
                image=message.content,
                prompt="請描述這張圖片"
            )
            
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