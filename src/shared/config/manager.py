import os
from typing import Dict, Optional, Type
from pathlib import Path
from functools import lru_cache
from .settings import Settings, get_settings
from .validator import ConfigValidator
from ..utils.logger import logger
from .base import BaseConfig
from .json_config import JSONConfig

class ConfigManager:
    """配置管理器"""
    
    def __init__(self, config_dir: Path):
        self.config_dir = config_dir
        self.config_dir.mkdir(parents=True, exist_ok=True)
        self._configs: Dict[str, BaseConfig] = {}
    
    def get_config(
        self,
        name: str,
        config_class: Type[BaseConfig] = JSONConfig
    ) -> BaseConfig:
        """獲取配置實例"""
        if name not in self._configs:
            config_path = self.config_dir / f"{name}.json"
            self._configs[name] = config_class(config_path)
        return self._configs[name]
    
    def save_all(self) -> bool:
        """保存所有配置"""
        success = True
        for name, config in self._configs.items():
            if not config.save():
                success = False
                logger.error(f"保存配置失敗: {name}")
        return success
    
    def reload_all(self):
        """重新載入所有配置"""
        for name in list(self._configs.keys()):
            config_class = type(self._configs[name])
            config_path = self.config_dir / f"{name}.json"
            self._configs[name] = config_class(config_path)
    
    def get_ai_config(self) -> BaseConfig:
        """獲取 AI 配置"""
        return self.get_config("ai")
    
    def get_app_config(self) -> BaseConfig:
        """獲取應用配置"""
        return self.get_config("app")
    
    def get_line_config(self) -> BaseConfig:
        """獲取 LINE 配置"""
        return self.get_config("line")

@lru_cache()
def get_config_manager() -> ConfigManager:
    """獲取配置管理器單例"""
    return ConfigManager(Path("config"))

# 創建全局配置管理器實例
config_manager = get_config_manager() 