import sys
from pathlib import Path
from typing import Optional

from loguru import logger

class LoggerManager:
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._configure_logger()
        return cls._instance

    def _configure_logger(self):
        # Remove default handler
        logger.remove()

        # Get configurations from environment
        log_level = os.getenv('LOG_LEVEL', 'INFO')
        log_path = os.getenv('LOG_PATH', 'logs')
        log_rotation = os.getenv('LOG_ROTATION', '500 MB')
        log_retention = os.getenv('LOG_RETENTION', '10 days')

        # Create logs directory if it doesn't exist
        Path(log_path).mkdir(parents=True, exist_ok=True)

        # Add console handler
        logger.add(
            sys.stdout,
            format="{time:YYYY-MM-DD HH:mm:ss} | {level: <8} | {name}:{function}:{line} - {message}",
            level=log_level,
            colorize=True
        )

        # Add file handler
        logger.add(
            f"{log_path}/app.log",
            rotation=log_rotation,
            retention=log_retention,
            format="{time:YYYY-MM-DD HH:mm:ss} | {level: <8} | {name}:{function}:{line} - {message}",
            level=log_level,
            encoding='utf-8'
        )

    @staticmethod
    def get_logger(name: Optional[str] = None):
        """Get a logger instance with an optional name."""
        return logger.bind(name=name or "default") 