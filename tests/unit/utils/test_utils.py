import pytest
import json
from pathlib import Path
from datetime import datetime, date
from uuid import uuid4
from src.shared.utils.helpers import Helper, JSONEncoder
from src.shared.utils.logger import LoggerConfig

def test_json_encoder():
    """測試 JSON 編碼器"""
    data = {
        "datetime": datetime(2024, 1, 1),
        "date": date(2024, 1, 1),
        "uuid": uuid4(),
        "path": Path("test/path"),
        "str": "test"
    }
    
    # 編碼
    encoded = json.dumps(data, cls=JSONEncoder)
    decoded = json.loads(encoded)
    
    # 驗證
    assert isinstance(decoded["datetime"], str)
    assert isinstance(decoded["date"], str)
    assert isinstance(decoded["uuid"], str)
    assert isinstance(decoded["path"], str)
    assert decoded["str"] == "test"

def test_json_operations(tmp_path):
    """測試 JSON 操作"""
    file_path = tmp_path / "test.json"
    test_data = {"test": "value"}
    
    # 保存
    assert Helper.save_json(test_data, file_path)
    assert file_path.exists()
    
    # 載入
    loaded = Helper.load_json(file_path)
    assert loaded == test_data
    
    # 載入不存在的文件
    assert Helper.load_json(
        tmp_path / "nonexistent.json",
        default={}
    ) == {}

def test_dict_merging():
    """測試字典合併"""
    dict1 = {
        "a": 1,
        "b": {
            "c": 2,
            "d": 3
        }
    }
    dict2 = {
        "b": {
            "d": 4,
            "e": 5
        },
        "f": 6
    }
    
    # 深度合併
    merged = Helper.merge_dicts(dict1, dict2)
    assert merged["a"] == 1
    assert merged["b"]["c"] == 2
    assert merged["b"]["d"] == 4
    assert merged["b"]["e"] == 5
    assert merged["f"] == 6
    
    # 淺層合併
    merged = Helper.merge_dicts(dict1, dict2, deep=False)
    assert merged["b"] == dict2["b"]

def test_text_truncation():
    """測試文本截斷"""
    text = "Hello, World!"
    
    # 不需要截斷
    assert Helper.truncate_text(text, 20) == text
    
    # 需要截斷
    truncated = Helper.truncate_text(text, 10)
    assert len(truncated) == 10
    assert truncated.endswith("...")

def test_logger_setup(tmp_path):
    """測試日誌設置"""
    log_file = tmp_path / "test.log"
    
    # 創建日誌器
    logger = LoggerConfig.setup_logger(
        "test_logger",
        log_file
    )
    
    # 寫入日誌
    test_message = "Test log message"
    logger.info(test_message)
    
    # 驗證文件
    assert log_file.exists()
    log_content = log_file.read_text()
    assert test_message in log_content 