import google.generativeai as genai
from typing import Dict, List, Optional, Generator
from .base import BaseModel, ModelResponse
from ..session.base import Message
from ..utils.logger import logger

class GoogleAIModel(BaseModel):
    """Google AI 模型適配器"""
    
    def __init__(
        self,
        api_key: str,
        model: str = "gemini-pro",
        **kwargs
    ):
        super().__init__(api_key, **kwargs)
        self.model_name = model
        genai.configure(api_key=api_key)
        self.model = genai.GenerativeModel(model)
    
    async def generate(
        self,
        messages: List[Message],
        **kwargs
    ) -> ModelResponse:
        """生成回應"""
        try:
            # 轉換消息格式
            chat = self.model.start_chat()
            for msg in messages:
                if msg.role == "user":
                    chat.send_message(msg.content)
                    
            # 生成回應
            response = chat.send_message(messages[-1].content)
            
            return ModelResponse(
                content=response.text,
                role="assistant",
                model=self.model_name,
                usage=None,  # Google AI 目前不提供 token 使用量
                raw_response=response
            )
            
        except Exception as e:
            logger.error(f"Google AI 生成失敗: {str(e)}")
            raise
    
    async def generate_stream(
        self,
        messages: List[Message],
        **kwargs
    ) -> Generator[str, None, None]:
        """流式生成回應"""
        try:
            chat = self.model.start_chat()
            for msg in messages[:-1]:
                if msg.role == "user":
                    chat.send_message(msg.content)
                    
            async for chunk in chat.send_message(
                messages[-1].content,
                stream=True
            ):
                if chunk.text:
                    yield chunk.text
                    
        except Exception as e:
            logger.error(f"Google AI 流式生成失敗: {str(e)}")
            raise
    
    async def count_tokens(self, text: str) -> int:
        """計算 token 數量"""
        try:
            result = self.model.count_tokens(text)
            return result.total_tokens
            
        except Exception as e:
            logger.error(f"計算 token 失敗: {str(e)}")
            return len(text) // 4  # 粗略估算
    
    async def validate(self) -> bool:
        """驗證模型配置"""
        try:
            # 嘗試一個簡單的生成
            response = self.model.generate_content("Test")
            return bool(response and response.text)
            
        except Exception as e:
            logger.error(f"Google AI 驗證失敗: {str(e)}")
            return False 