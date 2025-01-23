from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional
from ..utils.logger import logger

class BaseAIModel(ABC):
    """AI 模型基類"""
    def __init__(self):
        """初始化模型"""
        self.temperature: float = 0.7
        self.max_tokens: int = 1000
        self.top_p: float = 0.9
        if not hasattr(self, 'model_type'):
            raise ValueError("子類必須在調用 super().__init__() 之前設置 model_type")
        self._initialize()
    
    @abstractmethod
    def _initialize(self) -> None:
        """初始化模型（由子類實現）"""
        pass
    
    @abstractmethod
    def generate_response(self, messages: List[Dict[str, str]]) -> str:
        """生成回應（由子類實現）"""
        pass
    
    def validate_response(self, response: str) -> bool:
        """驗證回應"""
        if not response or not isinstance(response, str):
            return False
        return True
    
    def format_messages(self, messages: List[Dict[str, str]]) -> List[Dict[str, str]]:
        """格式化消息"""
        formatted = []
        for msg in messages:
            if all(key in msg for key in ["role", "content"]):
                formatted.append({
                    "role": msg["role"],
                    "content": msg["content"]
                })
        return formatted
    
    def handle_error(self, error: Exception) -> str:
        """處理錯誤"""
        error_message = f"模型錯誤: {str(error)}"
        logger.error(error_message)
        return "抱歉，處理您的請求時出現錯誤。請稍後再試。"
    
    @property
    def model_info(self) -> Dict[str, Any]:
        """獲取模型信息"""
        return {
            "type": self.model_type,
            "temperature": self.temperature,
            "max_tokens": self.max_tokens,
            "top_p": self.top_p
        }
    
    def update_settings(self, settings: Dict[str, Any]) -> None:
        """更新模型設置"""
        if "temperature" in settings:
            self.temperature = float(settings["temperature"])
        if "max_tokens" in settings:
            self.max_tokens = int(settings["max_tokens"])
        if "top_p" in settings:
            self.top_p = float(settings["top_p"]) 