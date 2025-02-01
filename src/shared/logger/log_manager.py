import logging
import sys
from pathlib import Path
from typing import Optional
from datetime import datetime
from logging.handlers import RotatingFileHandler
import json

class LogManager:
    """日誌管理器"""
    
    def __init__(
        self,
        log_level: str = "INFO",
        log_dir: str = "logs",
        max_bytes: int = 10 * 1024 * 1024,  # 10MB
        backup_count: int = 5
    ):
        self.log_level = getattr(logging, log_level.upper())
        self.log_dir = Path(log_dir)
        self.max_bytes = max_bytes
        self.backup_count = backup_count
        
        # 創建日誌目錄
        self.log_dir.mkdir(parents=True, exist_ok=True)
        
        # 設置根日誌器
        self._setup_root_logger()
        
        # 獲取日誌器實例
        self.logger = logging.getLogger("CAG")
    
    def _setup_root_logger(self) -> None:
        """設置根日誌器"""
        root_logger = logging.getLogger()
        root_logger.setLevel(self.log_level)
        
        # 清除現有的處理器
        root_logger.handlers.clear()
        
        # 添加控制台處理器
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setFormatter(self._create_formatter())
        root_logger.addHandler(console_handler)
        
        # 添加文件處理器
        file_handler = self._create_file_handler()
        root_logger.addHandler(file_handler)
    
    def _create_formatter(self) -> logging.Formatter:
        """創建日誌格式器"""
        return logging.Formatter(
            '%(asctime)s [%(levelname)s] %(name)s: %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
    
    def _create_file_handler(self) -> RotatingFileHandler:
        """創建文件處理器"""
        log_file = self.log_dir / f"cag_{datetime.now():%Y%m%d}.log"
        handler = RotatingFileHandler(
            log_file,
            maxBytes=self.max_bytes,
            backupCount=self.backup_count,
            encoding='utf-8'
        )
        handler.setFormatter(self._create_formatter())
        return handler
    
    def set_level(self, level: str) -> None:
        """設置日誌級別"""
        self.log_level = getattr(logging, level.upper())
        self.logger.setLevel(self.log_level)
        
    def log_dict(self, level: str, data: dict, message: Optional[str] = None) -> None:
        """記錄字典數據"""
        log_func = getattr(self.logger, level.lower())
        if message:
            log_func(f"{message}: {json.dumps(data, ensure_ascii=False)}")
        else:
            log_func(json.dumps(data, ensure_ascii=False)) 