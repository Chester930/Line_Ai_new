import openai
from typing import Dict, List, Optional, Generator
from .base import BaseModel, ModelResponse
from ..session.base import Message
from ..utils.logger import logger

class OpenAIModel(BaseModel):
    """OpenAI 模型適配器"""
    
    def __init__(
        self,
        api_key: str,
        model: str = "gpt-3.5-turbo",
        **kwargs
    ):
        super().__init__(api_key, **kwargs)
        self.model_name = model
        openai.api_key = api_key
    
    async def generate(
        self,
        messages: List[Message],
        **kwargs
    ) -> ModelResponse:
        """生成回應"""
        try:
            formatted_msgs = self._format_messages(messages)
            
            response = await openai.ChatCompletion.acreate(
                model=self.model_name,
                messages=formatted_msgs,
                **kwargs
            )
            
            return ModelResponse(
                content=response.choices[0].message.content,
                role="assistant",
                model=self.model_name,
                usage=response.usage,
                raw_response=response
            )
            
        except Exception as e:
            logger.error(f"OpenAI 生成失敗: {str(e)}")
            raise
    
    async def generate_stream(
        self,
        messages: List[Message],
        **kwargs
    ) -> Generator[str, None, None]:
        """流式生成回應"""
        try:
            formatted_msgs = self._format_messages(messages)
            
            async for chunk in await openai.ChatCompletion.acreate(
                model=self.model_name,
                messages=formatted_msgs,
                stream=True,
                **kwargs
            ):
                if chunk and chunk.choices[0].delta.content:
                    yield chunk.choices[0].delta.content
                    
        except Exception as e:
            logger.error(f"OpenAI 流式生成失敗: {str(e)}")
            raise
    
    async def count_tokens(self, text: str) -> int:
        """計算 token 數量"""
        try:
            # 使用 tiktoken 計算 token
            import tiktoken
            encoding = tiktoken.encoding_for_model(self.model_name)
            return len(encoding.encode(text))
            
        except Exception as e:
            logger.error(f"計算 token 失敗: {str(e)}")
            return len(text) // 4  # 粗略估算
    
    async def validate(self) -> bool:
        """驗證模型配置"""
        try:
            # 嘗試進行一個簡單的 API 調用
            await openai.Model.aretrieve(self.model_name)
            return True
            
        except Exception as e:
            logger.error(f"OpenAI 驗證失敗: {str(e)}")
            return False 