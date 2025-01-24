from typing import Dict, List, Optional
import openai
from ..base import BaseAIModel, AIResponse
from ...session.base import Message
from ...utils.logger import logger

class GPTModel(BaseAIModel):
    """OpenAI GPT 模型"""
    
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
    ) -> AIResponse:
        """生成回應"""
        try:
            formatted_msgs = self._format_messages(messages)
            
            response = await openai.ChatCompletion.acreate(
                model=self.model_name,
                messages=formatted_msgs,
                **kwargs
            )
            
            return AIResponse(
                content=response.choices[0].message.content,
                model=self.model_name,
                usage=response.usage,
                raw_response=response
            )
            
        except Exception as e:
            self._handle_error(e, "GPT 生成")
    
    async def validate(self) -> bool:
        """驗證模型配置"""
        try:
            # 嘗試獲取模型資訊
            await openai.Model.aretrieve(self.model_name)
            return True
            
        except Exception as e:
            logger.error(f"GPT 驗證失敗: {str(e)}")
            return False 