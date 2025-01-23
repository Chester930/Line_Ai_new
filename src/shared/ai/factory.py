from typing import Dict, Type
from .base import BaseAIModel
from .models.gemini import GeminiModel
from ..utils.logger import logger

class ModelFactory:
    """AI 模型工廠"""
    _models: Dict[str, Type[BaseAIModel]] = {
        'gemini': GeminiModel,
        # 暫時註釋掉未實現的模型
        # 'openai': OpenAIModel,
        # 'claude': ClaudeModel
    }
    
    @classmethod
    def register_model(cls, name: str, model_class: Type[BaseAIModel]) -> None:
        """註冊新的模型類型"""
        cls._models[name] = model_class
    
    def create_model(self, model_type: str) -> BaseAIModel:
        """創建 AI 模型實例"""
        try:
            if model_type not in self._models:
                raise ValueError(f"不支援的模型類型: {model_type}")
            
            model_class = self._models[model_type]
            return model_class()
        except Exception as e:
            logger.error(f"創建模型失敗: {str(e)}")
            raise
    
    @classmethod
    def get_available_models(cls) -> list:
        """獲取所有可用的模型類型"""
        return list(cls._models.keys())

# 全局模型工廠實例
model_factory = ModelFactory() 