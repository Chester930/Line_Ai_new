from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional
from ..utils.logger import logger
from dataclasses import dataclass
from enum import Enum
from ..session.base import Message

class ModelType(Enum):
    """AI 模型類型"""
    GEMINI = "gemini"
    GPT = "gpt"
    CLAUDE = "claude"

@dataclass
class AIResponse:
    """AI 響應數據類"""
    content: str  # 使用 content 作為主要內容字段
    model: ModelType
    tokens: int
    raw_response: Optional[Dict[str, Any]] = None
    error: Optional[str] = None

    @property
    def text(self) -> str:
        """兼容性屬性，返回 content"""
        return self.content

@dataclass
class ModelResponse:
    """模型回應數據類"""
    text: str
    usage: Dict[str, Any]
    model_info: Dict[str, Any]
    raw_response: Optional[Dict] = None

class BaseAIModel(ABC):
    """AI 模型基類"""
    
    def __init__(self, api_key: str, **kwargs):
        self.api_key = api_key
        self.config = kwargs
        self.model_name = "unknown"
    
    @abstractmethod
    async def generate(
        self,
        prompt: str,
        context: Optional[List[Dict]] = None,
        **kwargs
    ) -> ModelResponse:
        """生成回應"""
        pass
    
    @abstractmethod
    async def validate(self) -> bool:
        """驗證模型配置"""
        pass
    
    @abstractmethod
    async def generate_stream(
        self,
        messages: List[Message],
        **kwargs
    ):
        """流式生成回應"""
        pass
    
    @abstractmethod
    async def count_tokens(self, text: str) -> int:
        """計算 token 數量"""
        pass
    
    def _format_messages(
        self,
        messages: List[Message]
    ) -> List[Dict[str, str]]:
        """格式化消息"""
        return [
            {
                "role": msg.role,
                "content": msg.content
            }
            for msg in messages
        ]
    
    def _handle_error(self, error: Exception, context: str = ""):
        """處理錯誤"""
        error_msg = f"{context} 失敗: {str(error)}"
        logger.error(f"{self.model_name} - {error_msg}")
        raise AIModelError(error_msg)

class AIModelError(Exception):
    """AI 模型錯誤"""
    pass

class BaseModel(ABC):
    """AI 模型基類"""
    
    def __init__(self, api_key: str, **kwargs):
        self.api_key = api_key
        self.config = kwargs
    
    @abstractmethod
    async def generate(
        self,
        messages: List[Message],
        **kwargs
    ) -> ModelResponse:
        """生成回應"""
        pass
    
    @abstractmethod
    async def generate_stream(
        self,
        messages: List[Message],
        **kwargs
    ):
        """流式生成回應"""
        pass
    
    @abstractmethod
    async def count_tokens(self, text: str) -> int:
        """計算 token 數量"""
        pass
    
    @abstractmethod
    async def validate(self) -> bool:
        """驗證模型配置"""
        pass
    
    def _format_messages(
        self,
        messages: List[Message]
    ) -> List[Dict[str, str]]:
        """格式化消息"""
        return [
            {
                "role": msg.role,
                "content": msg.content
            }
            for msg in messages
        ] 