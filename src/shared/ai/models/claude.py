from typing import List, Dict, Optional, Any
import anthropic
from dataclasses import dataclass
import logging
from ...config.cag_config import ModelConfig
from ..base import BaseAIModel, ModelResponse, ModelType, Message
from ..factory import AIModelFactory
from ...exceptions import ModelError

logger = logging.getLogger(__name__)

@dataclass
class ClaudeConfig(ModelConfig):
    """Claude 模型配置"""
    model_name: str = "claude-3-opus-20240229"
    max_retries: int = 3
    request_timeout: int = 30

@AIModelFactory.register(ModelType.CLAUDE)
class ClaudeModel(BaseAIModel):
    """Claude 模型實現"""
    
    def __init__(self, config: ClaudeConfig):
        super().__init__(config.api_key)
        self.config = config
        self.name = "claude"
        
        # 初始化 Anthropic 客戶端
        self.client = anthropic.AsyncAnthropic(api_key=config.api_key)
    
    async def generate(
        self,
        prompt: str,
        context: Optional[List[Dict]] = None,
        **kwargs
    ) -> ModelResponse:
        """生成回應"""
        try:
            # 準備系統提示詞
            system_prompt = "You are Claude, a helpful AI assistant."
            
            # 準備消息列表
            messages = []
            if context:
                for msg in context:
                    messages.append({
                        "role": msg["role"],
                        "content": msg["content"]
                    })
            
            # 生成回應
            response = await self.client.messages.create(
                model=self.config.model_name,
                system=system_prompt,
                messages=messages,
                max_tokens=self.config.max_tokens,
                temperature=self.config.temperature,
                timeout=self.config.request_timeout,
                **kwargs
            )
            
            # 構建回應對象
            result = ModelResponse(
                text=response.content[0].text,
                usage={
                    "input_tokens": response.usage.input_tokens,
                    "output_tokens": response.usage.output_tokens,
                    "total_tokens": (
                        response.usage.input_tokens + 
                        response.usage.output_tokens
                    )
                },
                model_info={
                    "model": self.config.model_name,
                    "stop_reason": response.stop_reason,
                    "stop_sequence": response.stop_sequence
                }
            )
            
            return result
            
        except Exception as e:
            self._handle_error(e, "Claude 生成")
    
    async def generate_stream(
        self,
        messages: List[Message],
        **kwargs
    ):
        """流式生成回應"""
        try:
            formatted_messages = self._format_messages(messages)
            response = await self.client.messages.create(
                model=self.config.model_name,
                messages=formatted_messages,
                stream=True,
                **kwargs
            )
            
            async for chunk in response:
                if chunk.delta.text:
                    yield chunk.delta.text
                    
        except Exception as e:
            self._handle_error(e, "Claude 流式生成")
    
    async def count_tokens(self, text: str) -> int:
        """計算 token 數量"""
        try:
            result = await self.client.count_tokens(text)
            return result.count
        except Exception as e:
            self._handle_error(e, "Claude token 計算")
    
    async def validate(self) -> bool:
        """驗證模型配置"""
        try:
            response = await self.generate("Test")
            return bool(response and response.text)
        except Exception as e:
            logger.error(f"Claude 驗證失敗: {str(e)}")
            return False

    def _initialize(self) -> None:
        """初始化 Claude 模型"""
        try:
            self.model = self.config.model_name
        except Exception as e:
            logger.error(f"Claude 模型初始化失敗: {str(e)}")
            raise
    
    def generate_response(self, messages: List[Dict[str, str]]) -> str:
        """生成回應"""
        try:
            formatted_messages = self.format_messages(messages)
            prompt = self._build_prompt(formatted_messages)
            
            response = self.client.messages.create(
                model=self.model,
                messages=[{"role": "user", "content": prompt}],
                max_tokens=self.max_tokens,
                temperature=self.temperature
            )
            
            return response.content[0].text
        except Exception as e:
            return self.handle_error(e)
    
    def _build_prompt(self, messages: List[Dict[str, str]]) -> str:
        """構建提示詞"""
        prompt = ""
        for msg in messages:
            role = "Human" if msg["role"] == "user" else "Assistant"
            prompt += f"{role}: {msg['content']}\n"
        return prompt 