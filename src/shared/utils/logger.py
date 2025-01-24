import logging
import os
from pathlib import Path
from ..config.manager import config_manager
import sys
from typing import Optional
from logging.handlers import RotatingFileHandler
from functools import wraps
from time import time
from datetime import datetime

class LoggerConfig:
    """日誌配置"""
    
    @staticmethod
    def setup_logger(
        name: str = "ai_assistant",
        log_file: Optional[Path] = None
    ) -> logging.Logger:
        """設置日誌"""
        # 載入配置
        app_config = config_manager.get_app_config()
        log_config = app_config.get("logging", {})
        
        # 創建日誌器
        logger = logging.getLogger(name)
        logger.setLevel(log_config.get("level", "INFO"))
        
        # 設置格式
        formatter = logging.Formatter(
            log_config.get(
                "format",
                "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
            )
        )
        
        # 控制台處理器
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setFormatter(formatter)
        logger.addHandler(console_handler)
        
        # 文件處理器
        if log_file:
            log_file.parent.mkdir(parents=True, exist_ok=True)
            file_handler = logging.FileHandler(
                log_file,
                encoding='utf-8'
            )
            file_handler.setFormatter(formatter)
            logger.addHandler(file_handler)
        
        return logger

# 創建全局日誌器
logger = LoggerConfig.setup_logger()

# 導出 logger 實例
__all__ = ["logger"]

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