from abc import ABC, abstractmethod
from typing import Dict, Any, Optional, List
from dataclasses import dataclass
import logging

logger = logging.getLogger(__name__)

@dataclass
class PluginConfig:
    """插件配置"""
    name: str
    version: str
    enabled: bool = True
    settings: Dict[str, Any] = None

class BasePlugin(ABC):
    """插件基類"""
    
    def __init__(self, config: PluginConfig):
        self.config = config
        self.name = config.name
        self.version = config.version
        self.enabled = config.enabled
    
    @abstractmethod
    async def initialize(self) -> bool:
        """初始化插件"""
        pass
    
    @abstractmethod
    async def execute(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """執行插件"""
        pass
    
    @abstractmethod
    async def cleanup(self) -> None:
        """清理插件資源"""
        pass
    
    def is_enabled(self) -> bool:
        """檢查插件是否啟用"""
        return self.enabled
    
    def get_setting(self, key: str, default: Any = None) -> Any:
        """獲取插件設置"""
        if not self.config.settings:
            return default
        return self.config.settings.get(key, default)

class PluginError(Exception):
    """插件錯誤"""
    pass 