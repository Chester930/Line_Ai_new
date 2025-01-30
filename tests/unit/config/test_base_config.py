import pytest
from pathlib import Path
from typing import Dict, Optional
from pydantic import BaseModel
from src.shared.config.base import BaseConfig
import os

class TestConfig(BaseConfig):
    """測試用配置類"""
    app_name: str = "test_app"
    debug: bool = False
    port: int = 8000
    api_key: Optional[str] = None
    settings: Dict[str, str] = {}
    
    def _load_config(self) -> None:
        """測試用的加載配置方法"""
        pass
    
    def save(self) -> bool:
        """測試用的保存配置方法"""
        return True

def test_env_variables():
    """測試環境變量處理"""
    # 設置環境變量
    os.environ["APP_NAME"] = "env_app"
    os.environ["DEBUG"] = "true"
    os.environ["PORT"] = "9000"
    
    try:
        config = TestConfig()
        
        # 驗證環境變量是否正確加載
        assert config.app_name == "env_app"
        assert config.debug is True
        assert config.port == 9000
        
    finally:
        # 清理環境變量
        del os.environ["APP_NAME"]
        del os.environ["DEBUG"]
        del os.environ["PORT"]

def test_get_config_value():
    """測試獲取配置值"""
    config = TestConfig()
    
    # 測試獲取實例屬性
    assert config.get("app_name") == "test_app"
    assert config.get("debug") is False
    
    # 測試獲取不存在的值
    assert config.get("nonexistent") is None
    assert config.get("nonexistent", "default") == "default"
    
    # 測試獲取嵌套配置
    config._config = {"nested": {"key": "value"}}
    assert config.get("nested.key") == "value"
    assert config.get("nested.nonexistent") is None

def test_set_config_value():
    """測試設置配置值"""
    config = TestConfig()
    
    # 測試設置實例屬性
    assert config.set("app_name", "new_app")
    assert config.app_name == "new_app"
    
    # 測試設置嵌套配置
    assert config.set("nested.key", "value")
    assert config._config["nested"]["key"] == "value"
    
    # 測試無效的鍵值
    assert not config.set("", None)  # 空鍵
    assert not config.set(".", "value")  # 只有分隔符
    assert not config.set("nested.", "value")  # 結尾是分隔符
    assert not config.set(".key", "value")  # 開頭是分隔符
    assert not config.set("a..b", "value")  # 連續分隔符
    
    # 測試設置到非字典節點
    config._config["leaf"] = "value"
    assert not config.set("leaf.key", "value")  # 嘗試在非字典節點下設置值

def test_update_config():
    """測試更新配置"""
    config = TestConfig()
    
    # 更新實例屬性和配置字典
    update_data = {
        "app_name": "updated_app",
        "custom_key": "custom_value"
    }
    
    assert config.update(update_data)
    assert config.app_name == "updated_app"
    assert config._config["custom_key"] == "custom_value"

def test_to_dict():
    """測試轉換為字典"""
    config = TestConfig()
    config._config = {"custom_key": "custom_value"}
    
    result = config.to_dict()
    
    # 驗證實例屬性
    assert result["app_name"] == "test_app"
    assert result["debug"] is False
    assert result["port"] == 8000
    
    # 驗證配置字典
    assert result["custom_key"] == "custom_value"
    
    # 驗證 config_path 被排除
    assert "config_path" not in result

def test_get_fields():
    """測試獲取配置字段"""
    config = TestConfig()
    fields = config.get_fields()
    
    # 驗證字段數量
    assert len(fields) == 5  # app_name, debug, port, api_key, settings
    
    # 驗證字段屬性
    app_name_field = fields["app_name"]
    assert app_name_field.name == "app_name"
    assert app_name_field.type_ == str
    assert app_name_field.default == "test_app"
    
    # 驗證 config_path 被排除
    assert "config_path" not in fields 