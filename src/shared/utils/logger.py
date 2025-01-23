import logging
import os
from pathlib import Path
from ..config.config import config

def setup_logger(name: str) -> logging.Logger:
    """設置日誌記錄器"""
    logger = logging.getLogger(name)
    
    # 如果已經有處理器，直接返回
    if logger.handlers:
        return logger
    
    # 強制設置日誌級別
    logger.setLevel(logging.DEBUG)
    
    # 創建格式化器
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    # 添加控制台處理器
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)
    
    # 添加文件處理器
    if hasattr(config.settings, 'log_file') and config.settings.log_file:
        try:
            file_handler = logging.FileHandler(
                config.settings.log_file,
                encoding='utf-8'
            )
            file_handler.setFormatter(formatter)
            logger.addHandler(file_handler)
        except Exception as e:
            logger.error(f"無法創建日誌文件處理器: {str(e)}")
    
    return logger

# 創建全局日誌記錄器
logger = setup_logger('line_ai')

# 導出 logger 實例
__all__ = ["logger"] 