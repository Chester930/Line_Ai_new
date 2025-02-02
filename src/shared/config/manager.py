from typing import Dict, Any, Optional, Type, Union
from pathlib import Path
import os
import json
import logging
from pydantic import BaseModel
from .base import BaseConfig, ConfigError
from .validator import ConfigValidator, ValidationError
from .config import Settings
from ..utils.logger import logger

class ConfigManager:
    """配置管理器"""
    
    _instance = None
    _initialized = False

    def __new__(cls, *args, **kwargs):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    @property
    def settings(self):
        return self._settings

    def __init__(self, config_dir: Union[str, Path] = None):
        self.base_path = Path(config_dir) if config_dir else Path("config")
        self.environment = os.getenv("APP_ENV", "development")
        self._settings = self._load_settings()
        self.configs = {}
        self.validators = {}
        self._ensure_config_dir()
        
    def _load_settings(self) -> Any:
        """載入設置"""
        try:
            from .config import Settings
            return Settings()
        except Exception as e:
            logger.error(f"載入設置失敗: {str(e)}")
            return None
            
    def _ensure_config_dir(self) -> None:
        """確保配置目錄存在"""
        env_path = self.base_path / self.environment
        env_path.mkdir(parents=True, exist_ok=True)
    
    def _get_config_path(self, name: str) -> Path:
        """獲取配置文件路徑"""
        return self.base_path / self.environment / f"{name}.json"
    
    def register_config(
        self,
        name: str,
        config_class: Type[BaseConfig],
        filename: str = None,
        **kwargs
    ) -> BaseConfig:
        """註冊配置"""
        try:
            config_path = self._get_config_path(filename or f"{name}.json")
            config = config_class(config_path=str(config_path), **kwargs)
            self.configs[name] = config
            return config
        except Exception as e:
            raise ConfigError(f"註冊配置 {name} 失敗: {str(e)}")
    
    def get_config(self, name: str) -> Optional[BaseConfig]:
        """獲取配置
        
        Args:
            name: 配置名稱
            
        Returns:
            配置實例
            
        Raises:
            KeyError: 配置不存在時拋出
        """
        if name not in self.configs:
            raise KeyError(f"配置 {name} 不存在")
        return self.configs[name]
    
    def update_config(self, name: str, data: Dict[str, Any]) -> bool:
        """更新配置
        
        Args:
            name: 配置名稱
            data: 更新數據
            
        Returns:
            是否更新成功
        """
        try:
            config = self.get_config(name)
            
            # 驗證更新數據
            if self.validator:
                self.validator.validate(config, data)
            
            # 更新配置
            if config.update(data):
                logger.info(f"已更新配置: {name}")
                return True
            return False
            
        except Exception as e:
            logger.error(f"更新配置失敗: {str(e)}")
            return False
    
    def save_config(self, name: str) -> bool:
        """保存配置
        
        Args:
            name: 配置名稱
            
        Returns:
            是否保存成功
        """
        try:
            config = self.get_config(name)
            return config.save()
            
        except Exception as e:
            logger.error(f"保存配置失敗: {str(e)}")
            return False
    
    def load_config(
        self,
        name: str,
        env_prefix: str = None,
        schema: Type[BaseModel] = None
    ) -> Optional[BaseConfig]:
        """載入配置
        
        Args:
            name: 配置名稱
            env_prefix: 環境變量前綴
            schema: 配置模式
            
        Returns:
            配置實例
            
        Raises:
            ConfigError: 載入失敗時拋出
        """
        try:
            if name not in self.configs:
                raise ConfigError(f"配置 {name} 不存在")
            
            config = self.configs[name]
            
            # 設置環境變量前綴
            if env_prefix:
                config._env_prefix = env_prefix
                config._load_env_vars()
            
            # 驗證配置模式
            if schema:
                schema.model_validate(config.to_dict())
            
            return config
            
        except Exception as e:
            logger.error(f"載入配置失敗: {str(e)}")
            raise ConfigError(f"載入配置失敗: {str(e)}")
    
    def reload_config(self, name: str) -> bool:
        """重新載入配置
        
        Args:
            name: 配置名稱
            
        Returns:
            是否重載成功
        """
        try:
            config = self.configs.get(name)
            if not config:
                logger.warning(f"配置 {name} 不存在")
                return False
            
            # 重新載入
            config._load_config()
            
            # 重新驗證
            if self.validator:
                self.validator.validate(config)
            
            return True
            
        except Exception as e:
            logger.error(f"重載配置 {name} 失敗: {str(e)}")
            return False
    
    def reload_all(self) -> bool:
        """重新載入所有配置
        
        Returns:
            是否全部重載成功
        """
        success = True
        for name in self.configs:
            if not self.reload_config(name):
                success = False
        return success
    
    def get_environment(self) -> str:
        """獲取當前環境"""
        return os.getenv("APP_ENV", self.environment)
    
    def set_environment(self, environment: str) -> None:
        """設置環境
        
        Args:
            environment: 環境名稱
        """
        if environment != self.environment:
            self.environment = environment
            self._ensure_config_dir()
            self.reload_all()
    
    def validate_config_schema(self, config: BaseConfig) -> bool:
        """驗證配置模式
        
        Args:
            config: 配置實例
            
        Returns:
            是否驗證通過
            
        Raises:
            ConfigError: 驗證失敗時拋出
        """
        try:
            if self.validator:
                return self.validator.validate(config)
            return True
            
        except Exception as e:
            raise ConfigError(f"配置驗證失敗: {str(e)}")
    
    def save_all(self) -> bool:
        """保存所有配置
        
        Returns:
            是否全部保存成功
        """
        success = True
        for name in self.configs:
            if not self.save_config(name):
                success = False
        return success

    def get(self, key: str, default: Any = None) -> Any:
        """獲取配置值"""
        try:
            # 優先從環境變量獲取
            env_value = os.getenv(key)
            if env_value is not None:
                return env_value
                
            # 從設置中獲取
            if self._settings and hasattr(self._settings, key):
                return getattr(self._settings, key)
                
            return default
            
        except Exception as e:
            logger.error(f"獲取配置失敗: {str(e)}")
            return default
            
    def get_line_config(self) -> Dict:
        """獲取 LINE 配置"""
        return {
            "channel_secret": self.get("LINE_CHANNEL_SECRET"),
            "channel_access_token": self.get("LINE_CHANNEL_ACCESS_TOKEN")
        }

config_manager = ConfigManager() 