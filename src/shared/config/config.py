import os
from pathlib import Path
from typing import Any, Dict

import yaml
from dotenv import load_dotenv

class Config:
    _instance = None
    _config: Dict[str, Any] = {}

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._load_config()
        return cls._instance

    def _load_config(self):
        # 加載 .env 文件
        load_dotenv()

        # 從環境變數獲取配置文件路徑
        config_path = os.getenv('CONFIG_PATH', 'config/development/config.yaml')
        
        # 讀取 YAML 配置
        with open(config_path, 'r', encoding='utf-8') as f:
            self._config = yaml.safe_load(f)

        # 環境變數覆蓋
        self._override_from_env()

    def _override_from_env(self):
        # 這裡可以添加環境變數覆蓋邏輯
        pass

    def get(self, key: str, default: Any = None) -> Any:
        """獲取配置值"""
        try:
            keys = key.split('.')
            value = self._config
            for k in keys:
                value = value[k]
            return value
        except (KeyError, TypeError):
            return default

config = Config() 