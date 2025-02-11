from enum import Enum, auto
from typing import Dict, Any

class ModelType(Enum):
    """模型類型"""
    GEMINI = "gemini"
    GPT = "gpt"
    CLAUDE = "claude"

class MessageRole(Enum):
    """消息角色"""
    SYSTEM = "system"
    USER = "user"
    ASSISTANT = "assistant"

class EventType(Enum):
    """事件類型"""
    MESSAGE = "message"
    USER = "user"
    SYSTEM = "system"
    ERROR = "error"

class CacheType(Enum):
    """快取類型"""
    MEMORY = "memory"
    REDIS = "redis"
    FILE = "file"

# 默認配置
DEFAULT_CONFIG: Dict[str, Any] = {
    "app": {
        "debug": False,
        "host": "0.0.0.0",
        "port": 8000,
        "logging": {
            "level": "INFO",
            "format": "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
        }
    },
    "ai": {
        "default_provider": "gemini",
        "temperature": 0.7,
        "max_tokens": 1000,
        "timeout": 30
    },
    "cache": {
        "type": "memory",
        "ttl": 3600
    }
}

# 錯誤消息
ERROR_MESSAGES = {
    "config_not_found": "找不到配置文件",
    "invalid_config": "無效的配置格式",
    "api_error": "API 調用失敗",
    "timeout": "請求超時",
    "validation_error": "驗證失敗",
    "unknown_error": "未知錯誤"
} 