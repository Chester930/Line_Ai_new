from typing import List, Dict, Optional, Any, AsyncGenerator
import google.generativeai as genai
from dataclasses import dataclass
import logging
from ...config.cag_config import ModelConfig
from ...exceptions import ModelError
from ...utils.logger import logger
from ..base import BaseAIModel, ModelResponse, ModelType, Message
from ...session.base import AIResponse

@dataclass
class GeminiConfig(ModelConfig):
    """Gemini 模型配置"""
    api_key: str  # 必需參數
    name: str = "gemini"  # 覆蓋父類默認值
    model_name: str = "gemini-pro"  # 覆蓋父類默認值
    safety_settings: Optional[Dict] = None
    generation_config: Optional[Dict] = None
    max_tokens: int = 1000
    temperature: float = 0.7
    top_p: float = 0.95
    top_k: int = 40

class GeminiModel(BaseAIModel):
    """Gemini 模型實現"""
    
    def __init__(self, config: GeminiConfig):
        super().__init__(config.api_key)
        self.config = config
        self.name = "gemini"
        self.client = None
        self._initialize()
    
    def _initialize(self):
        """初始化 Gemini 客戶端"""
        try:
            genai.configure(api_key=self.config.api_key)
            self.client = genai.GenerativeModel(
                model_name=self.config.model_name,
                generation_config={
                    "max_output_tokens": self.config.max_tokens,
                    "temperature": self.config.temperature,
                    "top_p": self.config.top_p,
                    "top_k": self.config.top_k
                }
            )
            logger.info(f"Initialized Gemini model: {self.config.model_name}")
        except Exception as e:
            logger.error(f"Failed to initialize Gemini model: {str(e)}")
            raise ModelError(f"Initialization failed: {str(e)}")
    
    async def generate(
        self,
        prompt: str,
        context: Optional[List[Dict]] = None
    ) -> ModelResponse:
        """生成回應"""
        try:
            # 準備上下文
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
            
            # 生成回應
            response = await self.client.generate_content(
                messages,
                stream=False
            )
            
            # 解析回應
            return ModelResponse(
                text=response.text,
                usage={
                    "prompt_tokens": response.prompt_token_count,
                    "completion_tokens": response.candidates[0].token_count,
                    "total_tokens": response.prompt_token_count + response.candidates[0].token_count
                },
                model_info={
                    "model": self.config.model_name,
                    "finish_reason": "stop"
                }
            )
            
        except Exception as e:
            logger.error(f"Failed to generate response: {str(e)}")
            raise ModelError(f"Generation failed: {str(e)}")
    
    async def generate_stream(
        self,
        messages: List[Message],
        **kwargs
    ) -> AsyncGenerator[str, None]:
        """流式生成回應"""
        try:
            if not messages:
                raise ModelError("No messages provided")
            
            formatted_messages = []
            for msg in messages:
                formatted_messages.append({
                    "role": msg.role if isinstance(msg, Message) else msg["role"],
                    "parts": [msg.content if isinstance(msg, Message) else msg["content"]]
                })
            
            stream = await self.client.generate_content(
                formatted_messages,
                stream=True,
                **kwargs
            )
            
            async for chunk in stream:
                if hasattr(chunk, 'text') and chunk.text:
                    yield chunk.text
                    
        except Exception as e:
            logger.error(f"Failed to generate stream response: {str(e)}")
            raise ModelError(f"Stream generation failed: {str(e)}")
    
    async def count_tokens(self, text: str) -> int:
        """計算 tokens"""
        try:
            result = self.client.count_tokens(text)
            return result.total_tokens
        except Exception as e:
            logger.error(f"Failed to count tokens: {str(e)}")
            raise
    
    async def validate(self) -> bool:
        """驗證模型"""
        try:
            response = await self.generate("Test message")
            return True if response else False
        except Exception:
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

    async def generate_response(self, messages: List[Dict[str, str]]) -> str:
        """生成回應"""
        try:
            formatted_messages = self._format_messages(messages)
            prompt = self._build_prompt(formatted_messages)
            
            response = await self.client.generate_content(
                prompt,
                generation_config={
                    'temperature': self.config.temperature,
                    'top_p': self.config.top_p,
                    'max_output_tokens': self.config.max_tokens
                }
            )
            
            # 檢查響應對象
            if hasattr(response, 'text') and response.text:
                return response.text
            if hasattr(response, 'content') and response.content:
                return response.content
            if hasattr(response, 'parts'):
                for part in response.parts:
                    if isinstance(part, dict) and part.get('text'):
                        return part['text']
            
            # 嘗試從字典中獲取
            try:
                if hasattr(response, 'dict'):
                    response_dict = await response.dict() if callable(response.dict) else response.dict
                    if isinstance(response_dict, dict):
                        text = (response_dict.get('text') or 
                               response_dict.get('content') or 
                               next((p['text'] for p in response_dict.get('parts', []) if p.get('text')), ''))
                        if text:
                            return text
            except Exception:
                pass
            
            return ''
            
        except Exception as e:
            error_response = await self.handle_error(e)
            return error_response.text
    
    def _build_prompt(self, messages: List[Dict[str, str]]) -> str:
        """構建提示詞"""
        prompt = ""
        for msg in messages:
            role = "User" if msg["role"] == "user" else "Assistant"
            prompt += f"{role}: {msg['content']}\n"
        prompt += "Assistant: "
        return prompt

    def _format_messages(self, messages: List[Message]) -> List[Dict[str, Any]]:
        """格式化消息列表"""
        return [{
            "role": msg.role if isinstance(msg, Message) else msg["role"],
            "parts": [msg.content if isinstance(msg, Message) else msg["content"]]
        } for msg in messages]

    async def handle_error(self, error: Exception) -> AIResponse:
        """統一錯誤處理"""
        error_msg = f"Gemini model error: {str(error)}"
        logger.error(error_msg)
        return AIResponse(
            text="很抱歉，處理過程中發生錯誤。請稍後再試。",
            model=self.config.model_name,
            tokens=0,
            raw_response={"error": error_msg}
        ) 