from typing import List, Dict, Optional, Any
import openai
from dataclasses import dataclass
import logging
from ...config.cag_config import ModelConfig
from ..base import BaseAIModel, ModelResponse, ModelType, Message
from ..factory import AIModelFactory
from ...exceptions import ModelError

logger = logging.getLogger(__name__)

@dataclass
class GPTConfig(ModelConfig):
    """GPT 模型配置"""
    model_name: str = "gpt-4"
    organization: Optional[str] = None
    max_retries: int = 3
    request_timeout: int = 30

@AIModelFactory.register(ModelType.GPT)
class GPTModel(BaseAIModel):
    """GPT 模型實現"""
    
    def __init__(self, config: GPTConfig):
        super().__init__(config.api_key)
        self.config = config
        self.name = "gpt"
        
        # 初始化 OpenAI
        openai.api_key = config.api_key
        if config.organization:
            openai.organization = config.organization
            
    async def generate(
        self,
        prompt: str,
        context: Optional[List[Dict]] = None,
        **kwargs
    ) -> ModelResponse:
        """生成回應"""
        try:
            # 準備消息列表
            messages = []
            if context:
                messages.extend([
                    {"role": msg["role"], "content": msg["content"]}
                    for msg in context
                ])
            messages.append({"role": "user", "content": prompt})
            
            # 生成回應
            response = await openai.ChatCompletion.acreate(
                model=self.config.model_name,
                messages=messages,
                max_tokens=self.config.max_tokens,
                temperature=self.config.temperature,
                timeout=self.config.request_timeout,
                **kwargs
            )
            
            # 構建回應對象
            result = ModelResponse(
                text=response.choices[0].message.content,
                usage=response.usage,
                model_info={
                    "model": self.config.model_name,
                    "finish_reason": response.choices[0].finish_reason
                }
            )
            
            return result
            
        except Exception as e:
            self._handle_error(e, "GPT 生成")
    
    async def generate_stream(
        self,
        messages: List[Message],
        **kwargs
    ):
        """流式生成回應"""
        try:
            formatted_messages = self._format_messages(messages)
            response = await openai.ChatCompletion.acreate(
                model=self.config.model_name,
                messages=formatted_messages,
                stream=True,
                **kwargs
            )
            
            async for chunk in response:
                if chunk.choices[0].delta.content:
                    yield chunk.choices[0].delta.content
                    
        except Exception as e:
            self._handle_error(e, "GPT 流式生成")
    
    async def count_tokens(self, text: str) -> int:
        """計算 token 數量"""
        try:
            # 使用 tiktoken 計算 tokens
            import tiktoken
            encoding = tiktoken.encoding_for_model(self.config.model_name)
            return len(encoding.encode(text))
        except Exception as e:
            self._handle_error(e, "GPT token 計算")
    
    async def validate(self) -> bool:
        """驗證模型配置"""
        try:
            # 嘗試一個簡單的生成
            response = await self.generate("Test")
            return bool(response and response.text)
        except Exception as e:
            logger.error(f"GPT 驗證失敗: {str(e)}")
            return False 