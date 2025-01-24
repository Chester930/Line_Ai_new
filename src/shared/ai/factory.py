from typing import Optional, Type
from .base import BaseAIModel
from .models.gemini import GeminiModel
from .models.gpt import GPTModel
from .models.claude import ClaudeModel
from ..config.manager import config_manager
from ..utils.logger import logger

class AIModelFactory:
    """AI 模型工廠"""
    
    _models = {
        "gemini": GeminiModel,
        "gpt": GPTModel,
        "claude": ClaudeModel
    }
    
    @classmethod
    def create_model(
        cls,
        model_type: Optional[str] = None
    ) -> BaseAIModel:
        """創建 AI 模型實例"""
        try:
            # 載入 AI 配置
            ai_config = config_manager.get_ai_config()
            
            # 使用默認模型類型
            if not model_type:
                model_type = ai_config.get(
                    "default_provider",
                    "gemini"
                )
            
            # 獲取模型類
            model_class = cls._models.get(model_type)
            if not model_class:
                raise ValueError(f"不支持的模型類型: {model_type}")
            
            # 獲取模型配置
            model_config = ai_config.get(model_type, {})
            if not model_config:
                raise ValueError(f"找不到模型配置: {model_type}")
            
            # 創建模型實例
            model = model_class(
                api_key=model_config.get("api_key", ""),
                **model_config
            )
            
            logger.info(f"已創建 AI 模型: {model_type}")
            return model
            
        except Exception as e:
            logger.error(f"創建 AI 模型失敗: {str(e)}")
            raise
    
    @classmethod
    def register_model(
        cls,
        model_type: str,
        model_class: Type[BaseAIModel]
    ):
        """註冊新的模型類型"""
        cls._models[model_type] = model_class
        logger.info(f"已註冊新的模型類型: {model_type}")

# 全局模型工廠實例
model_factory = AIModelFactory() 