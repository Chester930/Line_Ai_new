from pydantic_settings import BaseSettings
from typing import Dict, Optional, List
from functools import lru_cache
from pathlib import Path

class Settings(BaseSettings):
    """應用程序設置"""
    
    # 基礎配置
    APP_NAME: str = "AI Chat Bot"
    VERSION: str = "1.0.0"
    DEBUG: bool = False
    
    # 路徑配置
    BASE_DIR: Path = Path(__file__).parent.parent.parent.parent
    LOG_DIR: Path = BASE_DIR / "logs"
    
    # LINE Bot 配置
    LINE_CHANNEL_SECRET: str
    LINE_CHANNEL_ACCESS_TOKEN: str
    
    # AI 模型配置
    GOOGLE_API_KEY: str
    OPENAI_API_KEY: Optional[str] = None
    ANTHROPIC_API_KEY: Optional[str] = None
    
    # 模型設置
    DEFAULT_MODEL: str = "gemini"
    MODEL_TIMEOUT: int = 30
    MAX_RETRIES: int = 3
    
    # 對話設置
    CONTEXT_LIMIT: int = 2000
    MEMORY_LIMIT: int = 500
    SESSION_TIMEOUT: int = 3600
    MAX_SESSIONS_PER_USER: int = 1
    
    # 安全設置
    API_KEY: Optional[str] = None
    ALLOWED_HOSTS: List[str] = ["*"]
    RATE_LIMIT: int = 60  # 每分鐘請求數
    
    # 日誌配置
    LOG_LEVEL: str = "INFO"
    LOG_FORMAT: str = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    LOG_FILE: Optional[str] = "app.log"
    
    # Redis 配置（預留）
    REDIS_URL: Optional[str] = None
    REDIS_PASSWORD: Optional[str] = None
    
    # 數據庫配置（預留）
    DATABASE_URL: Optional[str] = None
    
    class Config:
        env_file = ".env"
        case_sensitive = True

    def get_model_config(self, model_name: str) -> Dict:
        """獲取特定模型的配置"""
        base_config = {
            "timeout": self.MODEL_TIMEOUT,
            "max_retries": self.MAX_RETRIES
        }
        
        model_configs = {
            "gemini": {
                "api_key": self.GOOGLE_API_KEY,
                "temperature": 0.7,
                "max_tokens": 1000
            },
            "gpt": {
                "api_key": self.OPENAI_API_KEY,
                "temperature": 0.7,
                "max_tokens": 1000
            },
            "claude": {
                "api_key": self.ANTHROPIC_API_KEY,
                "temperature": 0.7,
                "max_tokens": 1000
            }
        }
        
        config = model_configs.get(model_name, {})
        return {**base_config, **config}

@lru_cache()
def get_settings() -> Settings:
    """獲取設置單例"""
    return Settings()

# 創建全局配置實例
settings = get_settings() 