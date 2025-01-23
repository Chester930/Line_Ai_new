import sys
from pathlib import Path
from loguru import logger

from ..config.config import config

def setup_logger():
    # 清除默認的處理器
    logger.remove()

    # 獲取日誌配置
    log_level = config.get('logging.level', 'INFO')
    log_format = config.get('logging.format', "<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - <level>{message}</level>")
    log_file = config.get('logging.file_path', 'logs/app.log')
    rotation = config.get('logging.rotation', '500 MB')
    retention = config.get('logging.retention', '10 days')

    # 確保日誌目錄存在
    log_path = Path(log_file).parent
    log_path.mkdir(parents=True, exist_ok=True)

    # 添加控制台輸出
    logger.add(
        sys.stdout,
        format=log_format,
        level=log_level,
        colorize=True
    )

    # 添加文件輸出
    logger.add(
        log_file,
        format=log_format,
        level=log_level,
        rotation=rotation,
        retention=retention
    )

    return logger

# 初始化日誌
logger = setup_logger()

# 導出 logger
__all__ = ['logger'] 