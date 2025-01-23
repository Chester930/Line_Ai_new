import pytest
import logging
import os
from pathlib import Path
from src.shared.utils.logger import setup_logger
from src.shared.config.config import config

@pytest.fixture
def temp_log_dir(tmp_path):
    """創建臨時日誌目錄"""
    log_dir = tmp_path / "logs"
    log_dir.mkdir(exist_ok=True)
    return log_dir

@pytest.fixture
def temp_log_file(temp_log_dir):
    """創建臨時日誌文件"""
    log_file = temp_log_dir / "test.log"
    original_log_file = config.settings.log_file
    original_log_level = config.settings.log_level
    
    # 設置測試配置
    config.settings.log_file = str(log_file)
    config.settings.log_level = "DEBUG"
    
    yield log_file
    
    # 恢復原始配置
    config.settings.log_file = original_log_file
    config.settings.log_level = original_log_level

def test_logger_initialization():
    """測試日誌初始化"""
    logger = setup_logger("test")
    assert isinstance(logger, logging.Logger)
    assert logger.name == "test"

def test_logger_levels(temp_log_file):
    """測試日誌級別"""
    logger = setup_logger("test_levels")
    assert logger.level == logging.DEBUG

def test_logger_levels(temp_log_file):
    """測試日誌級別"""
    config.settings.log_level = "DEBUG"  # 直接設置
    logger = setup_logger("test_levels")
    assert logger.level == logging.DEBUG

def test_logger_file_handler(temp_log_file):
    """測試文件處理器"""
    logger = setup_logger("test_file")
    
    # 驗證文件處理器
    has_file_handler = any(
        isinstance(h, logging.FileHandler) and 
        str(temp_log_file) in str(h.baseFilename)  # 修改比較方式
        for h in logger.handlers
    )
    assert has_file_handler, "找不到文件處理器"
    
    # 寫入日誌
    test_message = "測試消息"
    logger.info(test_message)
    
    # 驗證文件內容
    assert temp_log_file.exists(), "日誌文件未創建"
    log_content = temp_log_file.read_text(encoding='utf-8')
    assert test_message in log_content, "日誌消息未寫入文件"

def test_logger_error_handling(temp_log_dir):
    """測試錯誤處理"""
    # 使用無效的日誌文件路徑
    invalid_path = temp_log_dir / "invalid_dir" / "test.log"
    original_log_file = config.settings.log_file
    
    try:
        config.settings.log_file = str(invalid_path)
        logger = setup_logger("test_error")
        # 應該仍然創建成功，但只有控制台處理器
        assert logger.handlers, "日誌處理器未創建"
        assert any(isinstance(h, logging.StreamHandler) for h in logger.handlers), "未找到控制台處理器"
    finally:
        config.settings.log_file = original_log_file

def test_logger_multiple_initialization():
    """測試多次初始化"""
    logger1 = setup_logger("test_multiple")
    handlers_count = len(logger1.handlers)
    
    # 再次初始化相同名稱的日誌記錄器
    logger2 = setup_logger("test_multiple")
    
    # 應該是同一個日誌記錄器實例
    assert logger1 is logger2
    # 處理器數量應該保持不變
    assert len(logger2.handlers) == handlers_count