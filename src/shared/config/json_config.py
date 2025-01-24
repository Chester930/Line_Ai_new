import json
from pathlib import Path
from typing import Any, Dict, Optional
from .base import BaseConfig
from ..utils.logger import logger

class JSONConfig(BaseConfig):
    """JSON 配置"""
    
    def _load_config(self):
        """載入配置"""
        try:
            if not self.config_path:
                return
            
            if not self.config_path.exists():
                self.config_path.parent.mkdir(parents=True, exist_ok=True)
                self.config_path.write_text("{}")
            
            self._config = json.loads(self.config_path.read_text())
            logger.info(f"已載入配置: {self.config_path}")
            
        except Exception as e:
            logger.error(f"載入配置失敗: {str(e)}")
            self._config = {}
    
    def save(self) -> bool:
        """保存配置"""
        try:
            if not self.config_path:
                return False
            
            self.config_path.write_text(
                json.dumps(self._config, indent=2, ensure_ascii=False)
            )
            logger.info(f"已保存配置: {self.config_path}")
            return True
            
        except Exception as e:
            logger.error(f"保存配置失敗: {str(e)}")
            return False 