from typing import Any, Dict, Optional
from pathlib import Path
from abc import ABC, abstractmethod
from ..utils.logger import logger

class BaseConfig(ABC):
    """配置基類"""
    
    def __init__(self, config_path: Optional[Path] = None):
        self.config_path = config_path
        self._config: Dict[str, Any] = {}
        self._load_config()
    
    @abstractmethod
    def _load_config(self):
        """載入配置"""
        pass
    
    @abstractmethod
    def save(self) -> bool:
        """保存配置"""
        pass
    
    def get(self, key: str, default: Any = None) -> Any:
        """獲取配置值"""
        try:
            # 支持多層級鍵名，如 "openai.api_key"
            value = self._config
            for k in key.split('.'):
                value = value.get(k, {})
            return value if value != {} else default
        except Exception:
            return default
    
    def set(self, key: str, value: Any) -> bool:
        """設置配置值"""
        try:
            # 處理多層級鍵名
            keys = key.split('.')
            current = self._config
            
            # 遍歷到最後一層
            for k in keys[:-1]:
                current = current.setdefault(k, {})
            
            # 設置值
            current[keys[-1]] = value
            return True
        except Exception as e:
            logger.error(f"設置配置失敗: {str(e)}")
            return False
    
    def update(self, config: Dict[str, Any]) -> bool:
        """更新配置"""
        try:
            self._config.update(config)
            return True
        except Exception as e:
            logger.error(f"更新配置失敗: {str(e)}")
            return False
    
    def to_dict(self) -> Dict[str, Any]:
        """轉換為字典"""
        return self._config.copy() 