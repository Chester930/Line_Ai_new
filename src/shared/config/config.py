import os
import logging
from pathlib import Path
from typing import Any, Optional, Dict
from pydantic import BaseModel, ConfigDict
from pydantic_settings import BaseSettings
from functools import lru_cache

# 配置基本日誌
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class Settings(BaseSettings):
    """應用程式設定"""
    
    # 環境設定
    ENV: str = "development"
    DEBUG: bool = False
    ENVIRONMENT: str = "development"
    
    # 應用程式設定
    APP_NAME: str = "LINE AI Assistant"
    APP_PORT: int = 5000
    APP_HOST: str = "0.0.0.0"
    
    # 路徑設定
    CONFIG_PATH: str = "config/development/config.yaml"
    
    # 日誌設定
    LOG_LEVEL: str = "INFO"
    LOG_PATH: str = "logs"
    LOG_FORMAT: str = "%(asctime)s | %(levelname)-8s | %(name)s:%(funcName)s:%(lineno)d - %(message)s"
    LOG_ROTATION: str = "500 MB"
    LOG_RETENTION: str = "10 days"
    ERROR_REPORTING: bool = True
    ERROR_LOG_PATH: str = "logs/errors.log"
    
    # 監控設定
    ENABLE_MONITORING: bool = True
    PERFORMANCE_LOG_PATH: str = "logs/performance.log"
    
    # 資料庫設定
    DATABASE_URL: str = "sqlite:///test.db"
    DATABASE_ECHO: bool = False
    
    # 快取設定
    CACHE_TYPE: str = "memory"
    CACHE_TTL: int = 3600
    REDIS_URL: Optional[str] = "redis://localhost:6379/0"
    
    # LINE Bot 設定
    LINE_CHANNEL_SECRET: str
    LINE_CHANNEL_ACCESS_TOKEN: str
    LINE_BOT_HANDLER_PATH: str = "/webhook"
    
    # AI 模型設定
    DEFAULT_AI_MODEL: str = "Gemini 2.0 Flash"
    OPENAI_API_KEY: Optional[str] = None
    GOOGLE_API_KEY: str
    ANTHROPIC_API_KEY: Optional[str] = None
    
    # 模型參數
    MODEL_TEMPERATURE: float = 0.7
    MAX_TOKENS: int = 1000
    TOP_P: float = 0.9
    PRESENCE_PENALTY: float = 0.0
    FREQUENCY_PENALTY: float = 0.0
    
    # 向量存儲設定
    EMBEDDING_MODEL: str = "text-embedding-ada-002"
    VECTOR_STORE_TYPE: str = "faiss"
    CHUNK_SIZE: int = 500
    CHUNK_OVERLAP: int = 50
    
    # 開發工具設定
    NGROK_AUTHTOKEN: Optional[str] = None
    NGROK_REGION: str = "ap"
    
    # 安全設定
    ENABLE_RATE_LIMIT: bool = True
    RATE_LIMIT_REQUESTS: int = 100
    RATE_LIMIT_WINDOW: int = 3600
    
    # 會話管理
    SESSION_TIMEOUT: int = 3600
    SESSION_CLEANUP_INTERVAL: int = 86400
    
    # Webhook 安全
    WEBHOOK_SECRET: Optional[str] = None
    ALLOWED_IPS: str = "127.0.0.1,localhost"
    
    # 功能開關
    ENABLE_IMAGE_ANALYSIS: bool = True
    ENABLE_VOICE_RECOGNITION: bool = False
    ENABLE_MULTILINGUAL: bool = True
    ENABLE_GROUP_CHAT: bool = False
    
    CORS_ORIGINS: list = ["*"]  # 默認允許所有來源

    def get_app_config(self) -> Dict[str, Any]:
        """獲取應用程式配置"""
        return {
            "app_name": self.APP_NAME,
            "debug": self.DEBUG,
            "env": self.ENV
        }
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = False
        extra = "allow"  # 允許額外欄位

@lru_cache()
def get_settings() -> Settings:
    """獲取設定（使用緩存）"""
    return Settings()

# 創建全局配置實例
settings = get_settings()

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