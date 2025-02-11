from typing import List, Dict
import openai
from ...config.config import config
from ..base import BaseAIModel
from ...utils.logger import logger

class OpenAIModel(BaseAIModel):
    """OpenAI GPT 模型"""
    def __init__(self):
        self.model_type = "openai"
        super().__init__()
    
    def _initialize(self) -> None:
        """初始化 OpenAI 模型"""
        try:
            openai.api_key = config.settings.openai_api_key
            self.model = "gpt-4"  # 或其他模型
        except Exception as e:
            logger.error(f"OpenAI 模型初始化失敗: {str(e)}")
            raise
    
    def generate_response(self, messages: List[Dict[str, str]]) -> str:
        """生成回應"""
        try:
            formatted_messages = self.format_messages(messages)
            
            response = openai.ChatCompletion.create(
                model=self.model,
                messages=formatted_messages,
                temperature=self.temperature,
                max_tokens=self.max_tokens,
                top_p=self.top_p
            )
            
            return response.choices[0].message.content
        except Exception as e:
            return self.handle_error(e)
    
    def format_messages(self, messages: List[Dict[str, str]]) -> List[Dict[str, str]]:
        """格式化消息"""
        formatted = []
        for msg in messages:
            if "role" in msg and "content" in msg:
                formatted.append({
                    "role": msg["role"],
                    "content": msg["content"]
                })
        return formatted 