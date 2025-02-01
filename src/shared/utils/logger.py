import logging
import os
from pathlib import Path
from typing import Optional

# 基本日誌配置
DEFAULT_LOG_FORMAT = "%(asctime)s | %(levelname)-8s | %(name)s:%(funcName)s:%(lineno)d - %(message)s"
DEFAULT_LOG_LEVEL = "INFO"

def setup_logger(
    name: str,
    level: Optional[str] = None,
    log_format: Optional[str] = None,
    log_file: Optional[str] = None
) -> logging.Logger:
    """設置日誌記錄器"""
    logger = logging.getLogger(name)
    
    # 設置日誌級別
    log_level = getattr(logging, (level or DEFAULT_LOG_LEVEL).upper())
    logger.setLevel(log_level)
    
    # 設置格式化器
    formatter = logging.Formatter(
        log_format or DEFAULT_LOG_FORMAT
    )
    
    # 添加控制台處理器
    if not logger.handlers:
        console_handler = logging.StreamHandler()
        console_handler.setFormatter(formatter)
        logger.addHandler(console_handler)
        
        # 如果指定了日誌文件，添加文件處理器
        if log_file:
            log_path = Path(log_file)
            log_path.parent.mkdir(parents=True, exist_ok=True)
            
            file_handler = logging.FileHandler(log_file)
            file_handler.setFormatter(formatter)
            logger.addHandler(file_handler)
    
    return logger

# 創建默認日誌記錄器
logger = setup_logger(
    name="line_ai",
    level=os.getenv("LOG_LEVEL", DEFAULT_LOG_LEVEL),
    log_format=os.getenv("LOG_FORMAT", DEFAULT_LOG_FORMAT),
    log_file=os.getenv("LOG_FILE")
)

def get_logger(name: str) -> logging.Logger:
    """獲取命名的日誌記錄器"""
    return logging.getLogger(name) 