from typing import Dict, List, Optional
import anthropic
from ...config.config import config
from ..base import BaseAIModel, AIResponse
from ...session.base import Message
from ...utils.logger import logger

class ClaudeModel(BaseAIModel):
    """Anthropic Claude 模型"""
    
    def __init__(
        self,
        api_key: str,
        model: str = "claude-3-sonnet",
        **kwargs
    ):
        super().__init__(api_key, **kwargs)
        self.model_name = model
        self.client = anthropic.Anthropic(api_key=api_key)
    
    async def generate(
        self,
        messages: List[Message],
        **kwargs
    ) -> AIResponse:
        """生成回應"""
        try:
            # 轉換消息格式
            formatted_msgs = []
            for msg in messages:
                role = "user" if msg.role == "user" else "assistant"
                formatted_msgs.append({
                    "role": role,
                    "content": msg.content
                })
            
            # 生成回應
            response = await self.client.messages.create(
                model=self.model_name,
                messages=formatted_msgs,
                **kwargs
            )
            
            return AIResponse(
                content=response.content[0].text,
                model=self.model_name,
                usage=response.usage,
                raw_response=response
            )
            
        except Exception as e:
            self._handle_error(e, "Claude 生成")
    
    async def validate(self) -> bool:
        """驗證模型配置"""
        try:
            # 嘗試一個簡單的生成
            response = await self.client.messages.create(
                model=self.model_name,
                messages=[{
                    "role": "user",
                    "content": "Test"
                }]
            )
            return bool(response and response.content)
            
        except Exception as e:
            logger.error(f"Claude 驗證失敗: {str(e)}")
            return False

    def _initialize(self) -> None:
        """初始化 Claude 模型"""
        try:
            self.model = self.model_name
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