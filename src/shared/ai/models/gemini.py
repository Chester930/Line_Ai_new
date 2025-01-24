from typing import List, Dict, Optional
import google.generativeai as genai
from ...config.config import config
from ..base import BaseAIModel, ModelType, AIResponse
from ...utils.logger import logger
from ...factory import AIModelFactory
from ...session.base import Message

@AIModelFactory.register(ModelType.GEMINI)
class GeminiModel(BaseAIModel):
    """Google Gemini 模型實現"""
    
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
    ) -> AIResponse:
        """生成回應"""
        try:
            # 轉換消息格式
            chat = self.model.start_chat()
            for msg in messages[:-1]:  # 除了最後一條消息
                if msg.role == "user":
                    chat.send_message(msg.content)
            
            # 生成回應
            response = chat.send_message(messages[-1].content)
            
            return AIResponse(
                content=response.text,
                model=self.model_name,
                raw_response=response
            )
            
        except Exception as e:
            self._handle_error(e, "Gemini 生成")
    
    async def validate(self) -> bool:
        """驗證模型配置"""
        try:
            # 嘗試一個簡單的生成
            response = self.model.generate_content("Test")
            return bool(response and response.text)
            
        except Exception as e:
            logger.error(f"Gemini 驗證失敗: {str(e)}")
            return False
    
    async def analyze_image(
        self,
        image: bytes,
        prompt: str = None
    ) -> AIResponse:
        """分析圖片"""
        try:
            model = genai.GenerativeModel('gemini-pro-vision')
            response = await model.generate_content_async([image, prompt or "描述這張圖片"])
            return AIResponse(
                text=response.text,
                model=self.model_name,
                tokens=len(response.text.split()),
                raw_response=response.dict()
            )
        except Exception as e:
            logger.error(f"Gemini 圖片分析失敗: {str(e)}")
            return await self.handle_error(e)
    
    async def validate_response(
        self,
        response: Dict
    ) -> bool:
        """驗證響應"""
        return bool(response and response.get('text'))

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