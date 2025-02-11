import pytest
import logging
from src.shared.utils.logger import setup_logger
import os
import json

@pytest.fixture
def temp_log_file(tmp_path):
    """創建臨時日誌文件的 fixture"""
    log_file = tmp_path / "test.log"
    return str(log_file)

def test_logger_creation(temp_log_file):
    """測試日誌器創建"""
    logger = setup_logger("test_logger", log_file=temp_log_file)
    
    assert isinstance(logger, logging.Logger)
    assert logger.name == "test_logger"
    assert logger.level == logging.INFO
    assert os.path.exists(temp_log_file)

def test_log_levels(temp_log_file):
    """測試不同日誌級別"""
    logger = setup_logger("test_logger", log_file=temp_log_file)
    
    # 測試不同級別的日誌
    logger.debug("Debug message")
    logger.info("Info message")
    logger.warning("Warning message")
    logger.error("Error message")
    
    # 讀取日誌文件
    with open(temp_log_file, 'r', encoding='utf-8') as f:
        logs = f.readlines()
    
    # 由於默認級別是 INFO，debug 消息不應該出現
    assert len([log for log in logs if "Debug message" in log]) == 0
    assert len([log for log in logs if "Info message" in log]) == 1
    assert len([log for log in logs if "Warning message" in log]) == 1
    assert len([log for log in logs if "Error message" in log]) == 1

def test_log_formatting(temp_log_file):
    """測試日誌格式化"""
    logger = setup_logger("test_logger", log_file=temp_log_file)
    
    test_message = "Test log message"
    logger.info(test_message)
    
    with open(temp_log_file, 'r', encoding='utf-8') as f:
        log_line = f.readline()
    
    # 驗證日誌格式
    assert "INFO" in log_line
    assert "test_logger" in log_line
    assert test_message in log_line
    assert "[" in log_line and "]" in log_line  # 時間戳檢查

def test_structured_logging(temp_log_file):
    """測試結構化日誌"""
    logger = setup_logger("test_logger", log_file=temp_log_file)
    
    # 記錄結構化數據
    structured_data = {
        "user_id": "test_user",
        "action": "login",
        "status": "success"
    }
    logger.info("User action", extra=structured_data)
    
    with open(temp_log_file, 'r', encoding='utf-8') as f:
        log_line = f.readline()
    
    # 驗證結構化數據
    assert "test_user" in log_line
    assert "login" in log_line
    assert "success" in log_line

def test_error_logging_with_exception(temp_log_file):
    """測試異常日誌記錄"""
    logger = setup_logger("test_logger", log_file=temp_log_file)
    
    try:
        raise ValueError("Test error")
    except Exception as e:
        logger.exception("An error occurred")
    
    with open(temp_log_file, 'r', encoding='utf-8') as f:
        logs = f.readlines()
    
    # 驗證異常信息
    assert any("ValueError" in line for line in logs)
    assert any("Test error" in line for line in logs)
    assert any("Traceback" in line for line in logs) 