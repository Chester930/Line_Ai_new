import os
import logging
from pathlib import Path
from typing import Any, Optional, Dict
import yaml
from dotenv import load_dotenv
from pydantic import BaseModel

# 配置基本日誌
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class Settings(BaseModel):
    """應用程序設置"""
    app_name: str = "LINE AI Assistant Test"
    debug: bool = True
    line_channel_secret: str = "test_secret"
    line_channel_access_token: str = "test_token"
    database_url: str = "sqlite:///test.db"
    database_echo: bool = False
    google_api_key: str = "test_key"
    # 添加日誌配置
    log_level: str = "INFO"
    log_format: str = "%(asctime)s | %(levelname)-8s | %(name)s:%(funcName)s:%(lineno)d - %(message)s"
    log_file: Optional[str] = None

class Config:
    """配置管理器"""
    _instance = None
    _initialized = False

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self):
        if not self._initialized:
            self._config = {}
            self._load_config()
            self._initialized = True

    def _load_config(self):
        """加載配置"""
        # 加載默認配置
        self._config = {
            'app_name': 'LINE AI Assistant Test',
            'debug': True,
            'line': {
                'channel_secret': 'test_secret',
                'channel_access_token': 'test_token'
            },
            'database': {
                'url': 'sqlite:///test.db',
                'echo': False
            },
            'logging': {
                'level': 'INFO',
                'format': '%(asctime)s | %(levelname)-8s | %(name)s:%(funcName)s:%(lineno)d - %(message)s',
                'file': None
            }
        }
        
        # 加載環境變量
        if os.getenv('LINE_CHANNEL_SECRET'):
            self._config['line']['channel_secret'] = os.getenv('LINE_CHANNEL_SECRET')
        if os.getenv('LINE_CHANNEL_ACCESS_TOKEN'):
            self._config['line']['channel_access_token'] = os.getenv('LINE_CHANNEL_ACCESS_TOKEN')
        if os.getenv('DATABASE_URL'):
            self._config['database']['url'] = os.getenv('DATABASE_URL')
        if os.getenv('DATABASE_ECHO'):
            self._config['database']['echo'] = os.getenv('DATABASE_ECHO').lower() == 'true'
        if os.getenv('LOG_LEVEL'):
            self._config['logging']['level'] = os.getenv('LOG_LEVEL')
        if os.getenv('LOG_FORMAT'):
            self._config['logging']['format'] = os.getenv('LOG_FORMAT')
        if os.getenv('LOG_FILE'):
            self._config['logging']['file'] = os.getenv('LOG_FILE')

    def _merge_config(self, target: Dict, source: Dict) -> None:
        """合併配置"""
        for key, value in source.items():
            if key in target and isinstance(target[key], dict) and isinstance(value, dict):
                self._merge_config(target[key], value)
            else:
                target[key] = value

    def reload(self) -> None:
        """重新加載配置"""
        self._initialized = False
        self.__init__()

    def get(self, key: str, default: Any = None) -> Any:
        """獲取配置值"""
        try:
            parts = key.split('.')
            value = self._config
            for part in parts:
                value = value[part]
            return value
        except (KeyError, TypeError):
            return default

    @property
    def settings(self) -> Settings:
        """獲取設置對象"""
        return Settings(
            app_name=self.get('app_name', 'LINE AI Assistant Test'),
            debug=self.get('debug', True),
            line_channel_secret=self.get('line.channel_secret', 'test_secret'),
            line_channel_access_token=self.get('line.channel_access_token', 'test_token'),
            database_url=self.get('database.url', 'sqlite:///test.db'),
            database_echo=self.get('database.echo', False),
            google_api_key=os.getenv('GOOGLE_API_KEY', 'test_key'),
            log_level=self.get('logging.level', 'INFO'),
            log_format=self.get('logging.format', '%(asctime)s | %(levelname)-8s | %(name)s:%(funcName)s:%(lineno)d - %(message)s'),
            log_file=self.get('logging.file')
        )

# 創建全局配置實例
config = Config() 