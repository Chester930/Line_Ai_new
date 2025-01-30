import logging
import os
from pathlib import Path
from ..config import settings
import sys
from typing import Optional
from logging.handlers import RotatingFileHandler
from functools import wraps
from time import time
from datetime import datetime

class LoggerConfig:
    """日誌配置類"""
    
    @staticmethod
    def setup_logger(name: str = None) -> logging.Logger:
        """設置日誌記錄器"""
        # 使用傳入的名稱或模組名
        logger_name = name or __name__
        logger = logging.getLogger(logger_name)
        
        # 如果已經設置過處理器，直接返回
        if logger.handlers:
            return logger
            
        # 設置日誌級別
        logger.setLevel(getattr(logging, settings.LOG_LEVEL))
        
        # 確保日誌目錄存在
        log_dir = Path(settings.LOG_PATH)
        log_dir.mkdir(parents=True, exist_ok=True)
        
        # 創建日誌文件路徑
        log_file = log_dir / f"{logger_name}.log"
        
        # 創建處理器
        file_handler = RotatingFileHandler(
            filename=log_file,
            maxBytes=int(5e6),  # 5MB
            backupCount=5,
            encoding='utf-8'
        )
        console_handler = logging.StreamHandler()
        
        # 設置格式
        formatter = logging.Formatter(settings.LOG_FORMAT)
        file_handler.setFormatter(formatter)
        console_handler.setFormatter(formatter)
        
        # 添加處理器
        logger.addHandler(file_handler)
        logger.addHandler(console_handler)
        
        return logger

# 創建默認日誌記錄器
logger = LoggerConfig.setup_logger()

def get_logger(name: str = None) -> logging.Logger:
    """獲取日誌記錄器"""
    return LoggerConfig.setup_logger(name)

class Logger:
    """自定義日誌類"""
    
    def __init__(self, name: str = "app"):
        self.logger = logging.getLogger(name)
        self.logger.setLevel(logging.INFO)
        self._setup_console_handler()
    
    def _setup_console_handler(self):
        """設置控制台處理器"""
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setFormatter(self._get_formatter())
        self.logger.addHandler(console_handler)
    
    def add_file_handler(
        self,
        log_file: Path,
        level: str = "INFO",
        format: Optional[str] = None,
        max_bytes: int = 10_000_000,  # 10MB
        backup_count: int = 5
    ):
        """添加文件處理器"""
        try:
            # 創建日誌目錄
            log_file.parent.mkdir(parents=True, exist_ok=True)
            
            # 設置處理器
            file_handler = RotatingFileHandler(
                str(log_file),
                maxBytes=max_bytes,
                backupCount=backup_count
            )
            file_handler.setLevel(getattr(logging, level.upper()))
            file_handler.setFormatter(self._get_formatter(format))
            self.logger.addHandler(file_handler)
            
        except Exception as e:
            self.error(f"添加文件處理器失敗: {str(e)}")
    
    def _get_formatter(self, format_str: Optional[str] = None) -> logging.Formatter:
        """獲取格式化器"""
        default_format = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
        return logging.Formatter(format_str or default_format)
    
    def debug(self, message: str):
        """調試日誌"""
        self.logger.debug(message)
    
    def info(self, message: str):
        """信息日誌"""
        self.logger.info(message)
    
    def warning(self, message: str):
        """警告日誌"""
        self.logger.warning(message)
    
    def error(self, message: str):
        """錯誤日誌"""
        self.logger.error(message)
    
    def critical(self, message: str):
        """嚴重錯誤日誌"""
        self.logger.critical(message)

def log_execution_time(logger: Logger):
    """記錄執行時間的裝飾器"""
    def decorator(func):
        @wraps(func)
        async def async_wrapper(*args, **kwargs):
            start_time = time()
            try:
                result = await func(*args, **kwargs)
                execution_time = time() - start_time
                logger.info(f"{func.__name__} 執行時間: {execution_time:.2f}秒")
                return result
            except Exception as e:
                execution_time = time() - start_time
                logger.error(
                    f"{func.__name__} 執行失敗，耗時 {execution_time:.2f}秒: {str(e)}"
                )
                raise
        
        @wraps(func)
        def sync_wrapper(*args, **kwargs):
            start_time = time()
            try:
                result = func(*args, **kwargs)
                execution_time = time() - start_time
                logger.info(f"{func.__name__} 執行時間: {execution_time:.2f}秒")
                return result
            except Exception as e:
                execution_time = time() - start_time
                logger.error(
                    f"{func.__name__} 執行失敗，耗時 {execution_time:.2f}秒: {str(e)}"
                )
                raise
        
        return async_wrapper if asyncio.iscoroutinefunction(func) else sync_wrapper
    return decorator

# 創建全局日誌實例
logger = Logger()

# 配置日誌
logging.basicConfig(
    level=getattr(logging, settings.LOG_LEVEL),
    format=settings.LOG_FORMAT
)

logger = logging.getLogger(__name__) 