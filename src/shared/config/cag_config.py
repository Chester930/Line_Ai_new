from typing import Dict, Any, Optional
from dataclasses import dataclass
import json
import logging
from pathlib import Path

logger = logging.getLogger(__name__)

@dataclass
class ModelConfig:
    """模型配置基類"""
    api_key: str  # 必需參數放在前面
    name: str = "base"  # 可選參數放在後面
    model_name: str = "base"
    safety_settings: Optional[Dict] = None
    generation_config: Optional[Dict] = None
    max_tokens: int = 1000
    temperature: float = 0.7
    top_p: float = 0.95
    top_k: int = 40
    timeout: int = 30

    def __post_init__(self):
        """初始化後的驗證"""
        if self.temperature < 0 or self.temperature > 1:
            raise ValueError("Temperature must be between 0 and 1")
        if self.top_p < 0 or self.top_p > 1:
            raise ValueError("Top_p must be between 0 and 1")
        if self.max_tokens < 1:
            raise ValueError("Max_tokens must be greater than 0")

@dataclass
class CAGSystemConfig:
    """CAG 系統配置"""
    # 上下文配置
    max_context_length: int = 2000
    max_history_messages: int = 10
    
    # 記憶配置
    memory_ttl: int = 3600
    max_memory_items: int = 1000
    
    # 狀態配置
    enable_state_tracking: bool = True
    max_state_history: int = 100
    
    # 模型配置
    default_model: str = "gemini"
    models: Dict[str, ModelConfig] = None
    
    # 系統配置
    log_level: str = "INFO"
    enable_debug: bool = False

class ConfigManager:
    """配置管理器"""
    def __init__(self, config_path: Optional[str] = None):
        self.config_path = config_path or "config/cag_config.json"
        self.config: Optional[CAGSystemConfig] = None
    
    def load_config(self) -> CAGSystemConfig:
        """加載配置"""
        try:
            config_file = Path(self.config_path)
            if not config_file.exists():
                logger.warning(f"Config file not found: {self.config_path}")
                return self._create_default_config()
            
            with open(config_file, 'r', encoding='utf-8') as f:
                config_data = json.load(f)
            
            # 轉換模型配置
            models = {}
            for name, model_data in config_data.get("models", {}).items():
                models[name] = ModelConfig(**model_data)
            
            config_data["models"] = models
            
            self.config = CAGSystemConfig(**config_data)
            return self.config
            
        except Exception as e:
            logger.error(f"Failed to load config: {str(e)}")
            return self._create_default_config()
    
    def save_config(self) -> None:
        """保存配置"""
        if not self.config:
            return
            
        try:
            config_file = Path(self.config_path)
            config_file.parent.mkdir(parents=True, exist_ok=True)
            
            # 轉換為可序列化的字典
            config_dict = self._config_to_dict(self.config)
            
            with open(config_file, 'w', encoding='utf-8') as f:
                json.dump(config_dict, f, indent=2, ensure_ascii=False)
                
        except Exception as e:
            logger.error(f"Failed to save config: {str(e)}")
    
    def _create_default_config(self) -> CAGSystemConfig:
        """創建默認配置"""
        default_models = {
            "gemini": ModelConfig(
                name="gemini",
                api_key="YOUR_API_KEY",
                max_tokens=1000
            )
        }
        
        self.config = CAGSystemConfig(models=default_models)
        return self.config
    
    def _config_to_dict(self, config: CAGSystemConfig) -> Dict[str, Any]:
        """將配置對象轉換為字典"""
        config_dict = {
            "max_context_length": config.max_context_length,
            "max_history_messages": config.max_history_messages,
            "memory_ttl": config.memory_ttl,
            "max_memory_items": config.max_memory_items,
            "enable_state_tracking": config.enable_state_tracking,
            "max_state_history": config.max_state_history,
            "default_model": config.default_model,
            "log_level": config.log_level,
            "enable_debug": config.enable_debug,
            "models": {
                name: {
                    "name": model.name,
                    "api_key": model.api_key,
                    "max_tokens": model.max_tokens,
                    "temperature": model.temperature,
                    "timeout": model.timeout
                }
                for name, model in config.models.items()
            }
        }
        return config_dict 