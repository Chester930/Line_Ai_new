from typing import Optional, Type, Dict
from .base import BaseAIModel, ModelType
from ..config.manager import config_manager
from ..utils.logger import logger
from .models.gemini import GeminiModel
from enum import Enum

class ModelType(Enum):
    GEMINI = "gemini"
    GPT = "gpt"
    CLAUDE = "claude"

class AIModelFactory:
    """AI 模型工廠"""
    
    _models: Dict[ModelType, Type[BaseAIModel]] = {}
    
    @classmethod
    def register(cls, model_type: ModelType):
        """註冊模型類"""
        def wrapper(model_class: Type[BaseAIModel]):
            cls._models[model_type] = model_class
            return model_class
        return wrapper
    
    @classmethod
    async def create(cls, model_type: ModelType) -> BaseAIModel:
        """創建 AI 模型實例"""
        if model_type == ModelType.GEMINI:
            return GeminiModel()
        else:
            raise ValueError(f"不支持的模型類型: {model_type}")
    
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

class ModelFactory:
    """AI 模型工廠"""
    
    _models: Dict[str, Type[BaseAIModel]] = {
        "gemini": GeminiModel
    }
    
    @classmethod
    def register_model(cls, name: str, model_class: Type[BaseAIModel]):
        """註冊新的模型類型"""
        cls._models[name] = model_class
        logger.info(f"Registered new model type: {name}")
    
    @classmethod
    def create_model(cls, model_type: str, config: dict) -> BaseAIModel:
        """創建模型實例"""
        if model_type not in cls._models:
            raise ValueError(f"Unknown model type: {model_type}")
            
        model_class = cls._models[model_type]
        return model_class(config)

# 全局模型工廠實例
model_factory = AIModelFactory() 