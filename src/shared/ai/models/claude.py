from typing import List, Dict
import anthropic
from ...config.config import config
from ..base import BaseAIModel
from ...utils.logger import logger

class ClaudeModel(BaseAIModel):
    """Anthropic Claude 模型"""
    def __init__(self):
        self.model_type = "claude"
        super().__init__()
    
    def _initialize(self) -> None:
        """初始化 Claude 模型"""
        try:
            self.client = anthropic.Anthropic(api_key=config.settings.anthropic_api_key)
            self.model = "claude-3-opus-20240229"  # 或其他版本
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