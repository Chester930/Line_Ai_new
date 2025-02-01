import pytest
import logging
from pathlib import Path
import json
from src.shared.logger.log_manager import LogManager

class TestLogManager:
    def setup_method(self):
        self.test_log_dir = "tests/data/logs"
        self.log_manager = LogManager(log_dir=self.test_log_dir)
    
    def teardown_method(self):
        # 清理測試日誌文件
        log_dir = Path(self.test_log_dir)
        if log_dir.exists():
            for file in log_dir.glob("*.log*"):
                file.unlink()
            log_dir.rmdir()
    
    def test_logger_initialization(self):
        assert isinstance(self.log_manager.logger, logging.Logger)
        assert self.log_manager.logger.name == "CAG"
        assert self.log_manager.logger.level == logging.INFO
    
    def test_log_level_change(self):
        self.log_manager.set_level("DEBUG")
        assert self.log_manager.logger.level == logging.DEBUG
        
        self.log_manager.set_level("ERROR")
        assert self.log_manager.logger.level == logging.ERROR
    
    def test_log_file_creation(self):
        self.log_manager.logger.info("Test message")
        
        log_dir = Path(self.test_log_dir)
        log_files = list(log_dir.glob("*.log"))
        
        assert len(log_files) == 1
        assert log_files[0].exists()
    
    def test_log_dict_data(self):
        test_data = {
            "user_id": "test_user",
            "message": "Hello",
            "timestamp": "2024-03-21T10:00:00"
        }
        
        self.log_manager.log_dict("INFO", test_data, "Test dict logging")
        
        # 讀取日誌文件
        log_dir = Path(self.test_log_dir)
        log_file = next(log_dir.glob("*.log"))
        log_content = log_file.read_text(encoding='utf-8')
        
        # 驗證日誌內容
        assert "Test dict logging" in log_content
        assert "test_user" in log_content
        assert "Hello" in log_content 