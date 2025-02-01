from typing import Dict, Any, Optional
from dataclasses import dataclass
import json
from pathlib import Path
import logging

logger = logging.getLogger(__name__)

@dataclass
class PluginSettings:
    """插件設置"""
    enabled: bool = True
    version: str = "1.0"
    settings: Optional[Dict[str, Any]] = None

class PluginConfigManager:
    """插件配置管理器"""
    
    def __init__(self, config_path: str = "config/plugins_config.json"):
        self.config_path = Path(config_path)
        self.configs: Dict[str, PluginSettings] = {}
    
    def load_configs(self) -> None:
        """載入插件配置"""
        try:
            if not self.config_path.exists():
                logger.warning(f"插件配置文件不存在: {self.config_path}")
                return
            
            with open(self.config_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            for name, config in data.get("plugins", {}).items():
                self.configs[name] = PluginSettings(
                    enabled=config.get("enabled", True),
                    version=config.get("version", "1.0"),
                    settings=config.get("settings")
                )
                
        except Exception as e:
            logger.error(f"載入插件配置失敗: {str(e)}")
            raise
    
    def save_configs(self) -> None:
        """保存插件配置"""
        try:
            config_data = {
                "plugins": {
                    name: {
                        "enabled": config.enabled,
                        "version": config.version,
                        "settings": config.settings
                    }
                    for name, config in self.configs.items()
                }
            }
            
            self.config_path.parent.mkdir(parents=True, exist_ok=True)
            with open(self.config_path, 'w', encoding='utf-8') as f:
                json.dump(config_data, f, indent=2, ensure_ascii=False)
                
        except Exception as e:
            logger.error(f"保存插件配置失敗: {str(e)}")
            raise
    
    def get_plugin_config(self, name: str) -> Optional[PluginSettings]:
        """獲取插件配置"""
        return self.configs.get(name)
    
    def update_plugin_config(
        self,
        name: str,
        settings: Dict[str, Any]
    ) -> None:
        """更新插件配置"""
        if name in self.configs:
            self.configs[name].settings.update(settings)
            self.save_configs() 