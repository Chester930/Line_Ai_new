from typing import List, Dict
import google.generativeai as genai
from ...config.config import config
from ..base import BaseAIModel
from ...utils.logger import logger

class GeminiModel(BaseAIModel):
    """Google Gemini 模型"""
    def __init__(self):
        # 先設置 model_type，再調用父類初始化
        self.model_type = "gemini"
        super().__init__()
    
    def _initialize(self) -> None:
        """初始化 Gemini 模型"""
        try:
            genai.configure(api_key=config.settings.google_api_key)
            self.model = genai.GenerativeModel('gemini-pro')
            logger.info("Gemini 模型初始化成功")
        except Exception as e:
            logger.error(f"Gemini 模型初始化失敗: {str(e)}")
            raise
    
    def generate_response(self, messages: List[Dict[str, str]]) -> str:
        """生成回應"""
        try:
            formatted_messages = self.format_messages(messages)
            prompt = self._build_prompt(formatted_messages)
            
            response = self.model.generate_content(
                prompt,
                generation_config={
                    'temperature': self.temperature,
                    'top_p': self.top_p,
                    'max_output_tokens': self.max_tokens
                }
            )
            
            return response.text
        except Exception as e:
            return self.handle_error(e)
    
    def _build_prompt(self, messages: List[Dict[str, str]]) -> str:
        """構建提示詞"""
        prompt = ""
        for msg in messages:
            role = "User" if msg["role"] == "user" else "Assistant"
            prompt += f"{role}: {msg['content']}\n"
        prompt += "Assistant: "
        return prompt 