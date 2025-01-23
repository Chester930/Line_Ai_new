import pytest
from src.shared.utils.logger import logger

def test_logger():
    logger.debug("Debug message")
    logger.info("Info message")
    logger.warning("Warning message")
    logger.error("Error message")
    # 如果沒有拋出異常，則測試通過 