from typing import List, Dict, Optional, Any
import google.generativeai as genai
from dataclasses import dataclass
import logging
from ...config.cag_config import ModelConfig
from ...exceptions import ModelError
from ...utils.logger import logger
from ..base import BaseAIModel, ModelResponse, ModelType, Message
from ...session.base import AIResponse
from ..factory import AIModelFactory

logger = logging.getLogger(__name__)

@dataclass
class GeminiConfig(ModelConfig):
    """Gemini 模型配置"""
    model_name: str = "gemini-pro"
    safety_settings: Optional[Dict] = None
    generation_config: Optional[Dict] = None

@AIModelFactory.register(ModelType.GEMINI)
class GeminiModel(BaseAIModel):
    """Gemini 模型實現"""
    
    def __init__(self, config: GeminiConfig):
        super().__init__(config.api_key)
        self.config = config
        self.name = "gemini"
        
        # 初始化 Gemini
        genai.configure(api_key=config.api_key)
        
        # 創建模型實例
        generation_config = {
            "max_output_tokens": config.max_tokens,
            "temperature": config.temperature,
            **config.generation_config or {}
        }
        
        self.model = genai.GenerativeModel(
            model_name=config.model_name,
            generation_config=generation_config,
            safety_settings=config.safety_settings
        )
    
    async def generate(
        self,
        prompt: str,
        context: Optional[List[Dict]] = None,
        **kwargs
    ) -> ModelResponse:
        """生成回應"""
        try:
            # 準備對話歷史
            messages = []
            if context:
                for msg in context:
                    messages.append({
                        "role": msg["role"],
                        "parts": [msg["content"]]
                    })
            
            # 添加當前提示
            messages.append({
                "role": "user",
                "parts": [prompt]
            })
            
            # 創建對話
            chat = self.model.start_chat(history=messages)
            
            # 生成回應
            response = chat.send_message(
                prompt,
                stream=False,
                **kwargs
            )
            
            # 構建回應對象
            result = ModelResponse(
                text=response.text,
                usage={
                    "prompt_tokens": response.prompt_token_count,
                    "completion_tokens": response.candidates[0].token_count,
                    "total_tokens": (
                        response.prompt_token_count + 
                        response.candidates[0].token_count
                    )
                },
                model_info={
                    "model": self.config.model_name,
                    "safety_ratings": [
                        {
                            "category": rating.category,
                            "probability": rating.probability
                        }
                        for rating in response.prompt_feedback.safety_ratings
                    ]
                }
            )
            
            return result
            
        except Exception as e:
            logger.error(f"Gemini generation error: {str(e)}", exc_info=True)
            raise ModelError(f"Failed to generate response: {str(e)}")
    
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
                model=self.config.model_name,
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

    async def generate_stream(
        self,
        messages: List[Message],
        **kwargs
    ):
        """流式生成回應"""
        try:
            formatted_messages = self._format_messages(messages)
            response = self.model.generate_content(
                formatted_messages[-1].content,
                stream=True,
                **kwargs
            )
            
            async for chunk in response:
                if chunk.text:
                    yield chunk.text
                    
        except Exception as e:
            self._handle_error(e, "流式生成")
    
    async def count_tokens(self, text: str) -> int:
        """計算 token 數量"""
        try:
            result = self.model.count_tokens(text)
            return result.total_tokens
        except Exception as e:
            self._handle_error(e, "計算 tokens") 