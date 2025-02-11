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
import aiofiles
import asyncio

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

    def __init__(self, config_dir: Union[str, Path] = "config"):
        if not self._initialized:
            self.base_path = Path(config_dir)
            self.configs: Dict[str, BaseConfig] = {}
            self.validators: Dict[str, ConfigValidator] = {}
            self._environment = "development"
            self._settings = self._load_settings()
            self._ensure_config_dir()
            self._config = {}
            self._loaded = False
            self._initialized = True
        
    def _load_settings(self) -> Any:
        """載入設置"""
        try:
            return Settings()
        except Exception as e:
            logger.error(f"載入設置失敗: {str(e)}")
            return None
            
    def _ensure_config_dir(self) -> None:
        """確保配置目錄存在"""
        env_path = self.base_path / self._environment
        env_path.mkdir(parents=True, exist_ok=True)
    
    def _get_config_path(self, name: str) -> Path:
        """獲取配置文件路徑"""
        config_dir = self.base_path / self._environment
        config_dir.mkdir(parents=True, exist_ok=True)
        return config_dir / name
    
    def _apply_env_override(self, config: BaseConfig, prefix: str) -> None:
        """應用環境變量覆蓋"""
        for key in dir(config):
            if key.startswith('_'):
                continue
            
            env_key = f"{prefix}{key.upper()}"
            env_value = os.getenv(env_key)
            
            if env_value is not None:
                # 獲取字段信息
                field_info = config.model_fields.get(key)
                if field_info:
                    # 轉換值為正確類型
                    value = config._convert_value(env_value, field_info)
                    setattr(config, key, value)
                    # 同時更新配置字典
                    config._config[key] = value
                    # 保存更改
                    asyncio.create_task(config.save())

    async def register_config(
        self,
        name: str,
        config_class: Type[BaseConfig],
        filename: str = None,
        validator: ConfigValidator = None,
        data: Dict[str, Any] = None,
        **kwargs
    ) -> BaseConfig:
        """註冊配置"""
        try:
            config_path = self._get_config_path(filename or f"{name}.json")
            config = config_class(
                path=str(config_path),
                data=data,
                env_prefix=kwargs.pop('env_prefix', f"{self._environment}_"),
                **kwargs
            )
            config.config_path = str(config_path)
            
            if not config.is_loaded:
                await config.load()
            
            self.configs[name] = config
            if validator:
                self.validators[name] = validator
            return config
        except Exception as e:
            logger.error(f"註冊配置失敗: {str(e)}")
            raise ConfigError(f"註冊配置 {name} 失敗") from e

    async def get_config(self, name: str) -> BaseConfig:
        """獲取配置"""
        if name not in self.configs:
            raise ConfigError(f"配置 {name} 不存在")
        
        config = self.configs[name]
        # 確保配置已加載
        if not config.is_loaded:  # 使用修改後的屬性名稱
            if not await config.load():
                raise ConfigError(f"載入配置 {name} 失敗")
        
        return config
    
    async def update_config(self, name: str, data: Dict[str, Any]) -> bool:
        """更新配置"""
        if name not in self.configs:
            raise ConfigError(f"配置 {name} 不存在")
        
        try:
            config = self.configs[name]
            for key, value in data.items():
                setattr(config, key, value)
            
            # 保存配置
            return await config.save()
        except Exception as e:
            logger.error(f"更新配置失敗: {str(e)}")
            return False
    
    async def save_config(self, name: str, data: Dict[str, Any] = None) -> bool:
        """保存配置"""
        if name not in self.configs:
            raise ConfigError(f"配置 {name} 不存在")
        
        config = self.configs[name]
        if data:
            for key, value in data.items():
                setattr(config, key, value)
        
        try:
            await config.save()
            return True
        except Exception as e:
            logger.error(f"保存配置失敗: {str(e)}")
            return False
    
    async def load_config(
        self,
        name: str,
        env_prefix: str = None,
        schema: Type[BaseModel] = None,
        data: Dict[str, Any] = None
    ) -> bool:
        """載入配置"""
        try:
            if name not in self.configs:
                # 如果是環境配置，自動創建
                if name in ["development", "production", "test"]:
                    # 先創建環境配置
                    env_config = await self.register_config(name, BaseConfig, f"{name}.json")
                    await env_config.save()
                    
                    # 再創建 app 配置
                    app_config = await self.register_config("app", BaseConfig, "app.json")
                    if data:
                        # 更新配置數據
                        for key, value in data.items():
                            setattr(app_config, key, value)
                        await app_config.save()
                        
                        # 確保數據已加載
                        await app_config.load()
                        
                        # 驗證模式
                        if schema:
                            try:
                                # 構建驗證數據
                                app_config = self.configs.get("app")
                                if app_config:
                                    validate_data = {"app": {
                                        "name": getattr(app_config, "name", None),
                                        "debug": getattr(app_config, "debug", False)
                                    }}
                                    schema.model_validate(validate_data)
                            except Exception as e:
                                raise ConfigError(f"配置驗證失敗: {str(e)}")
                else:
                    raise ConfigError(f"配置 {name} 不存在")
            
            config = self.configs[name]
            success = await config.load()
            
            # 應用環境變量
            if env_prefix:
                self._apply_env_override(config, env_prefix)
                await config.save()  # 保存環境變量覆蓋的更改
            
            return success
        except Exception as e:
            logger.error(f"載入配置失敗: {str(e)}")
            raise ConfigError(f"載入配置失敗: {str(e)}")
    
    async def reload_config(self, name: str) -> bool:
        """改進的重新載入邏輯"""
        config = self.configs.get(name)
        if not config:
            return False
        
        try:
            # 使用現有配置的路徑重新初始化
            new_config = config.__class__(path=config.config_path)
            new_config.config_path = config.config_path  # 確保路徑被繼承
            if await new_config.load():
                self.configs[name] = new_config
                return True
            return False
        except Exception as e:
            logger.error(f"重載配置失敗: {str(e)}")
            return False
    
    async def reload_all(self) -> bool:
        """重新載入所有配置"""
        success = True
        for name in self.configs:
            if not await self.reload_config(name):
                success = False
        return success
    
    def get_environment(self) -> str:
        """獲取當前環境"""
        return self._environment
    
    async def set_environment(self, environment: str) -> None:
        """設置環境"""
        if environment not in ["development", "production", "test"]:
            raise ConfigError(f"無效的環境名稱: {environment}")
        
        try:
            if environment != self._environment:
                # 保存當前環境配置
                await self.save_all()
                
                # 切換環境
                self._environment = environment
                self._ensure_config_dir()
                
                # 確保環境配置存在
                if environment not in self.configs:
                    await self.register_config(environment, BaseConfig, f"{environment}.json")
                    await self.register_config("app", BaseConfig, "app.json")  # 同時創建 app 配置
                
                # 重新載入所有配置
                await self.reload_all()
                
        except Exception as e:
            logger.error(f"切換環境失敗: {str(e)}")
            raise ConfigError(f"切換環境失敗: {str(e)}")
    
    def validate_config_schema(self, config: Dict[str, Any], schema: Type[BaseModel]) -> bool:
        """驗證配置模式"""
        try:
            schema.model_validate(config)
            return True
            
        except Exception as e:
            logger.error(f"配置模式驗證失敗: {str(e)}")
            raise ValidationError(str(e))
    
    async def save_all(self) -> bool:
        """保存所有配置"""
        try:
            # 並行保存所有配置
            results = await asyncio.gather(
                *(config.save() for config in self.configs.values()),
                return_exceptions=True
            )
            # 檢查所有結果
            for result in results:
                if isinstance(result, Exception):
                    raise result
                if not result:
                    return False
            return True
        except Exception as e:
            logger.error(f"保存所有配置失敗: {str(e)}")
            return False

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

    async def delete_config(self, name: str) -> bool:
        """刪除配置"""
        if name not in self.configs:
            raise ConfigError(f"配置 {name} 不存在")
        
        try:
            config = self.configs[name]
            config_path = Path(config.config_path)
            if config_path.exists():
                config_path.unlink()
            del self.configs[name]
            return True
        except Exception as e:
            logger.error(f"刪除配置 {name} 失敗: {str(e)}")
            return False

    async def validate_config(self, name: str) -> bool:
        """驗證配置"""
        if name not in self.configs:
            raise ConfigError(f"配置 {name} 不存在")
        
        try:
            config = self.configs[name]
            config_dict = config.__dict__ if not isinstance(config, dict) else config
            
            # 使用驗證器
            if name in self.validators:
                validator = self.validators[name]
                if not await validator.validate(config_dict):
                    raise ConfigError(f"配置 {name} 驗證失敗")
            
            # 基本驗證
            for key, value in config_dict.items():
                if key.startswith('_'):  # 跳過私有屬性
                    continue
                if value is None:
                    raise ValidationError(f"配置項 {key} 不能為空")
                    
                # 檢查字段類型
                field_info = config.model_fields.get(key)
                if field_info:
                    try:
                        config._convert_value(value, field_info)
                    except (ValueError, TypeError):
                        raise ValidationError(f"配置項 {key} 類型錯誤")
                    
            return True
        except Exception as e:
            logger.error(f"配置驗證失敗: {str(e)}")
            raise ConfigError(f"配置驗證失敗: {str(e)}")

    def load(self) -> Dict[str, Any]:
        """載入配置"""
        if not self._loaded:
            try:
                # 實現配置載入邏輯
                self._config = {
                    "LINE_CHANNEL_SECRET": os.getenv("LINE_CHANNEL_SECRET", "test_secret"),
                    "LINE_CHANNEL_ACCESS_TOKEN": os.getenv("LINE_CHANNEL_ACCESS_TOKEN", "test_token"),
                }
                self._loaded = True
            except Exception as e:
                logger.error(f"載入配置失敗: {str(e)}")
                return None
        return self._config

    async def async_load(self) -> Dict[str, Any]:
        """異步載入配置"""
        try:
            return self.load()
        except Exception as e:
            logger.error(f"異步載入配置失敗: {str(e)}")
            return None

config_manager = ConfigManager() 