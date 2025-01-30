import pytest
from pathlib import Path
import tempfile
import json
from typing import Dict, Optional
from pydantic import BaseModel, Field

from src.shared.config.manager import ConfigManager
from src.shared.config.json_config import JSONConfig
from src.shared.config.validator import ConfigValidator, ValidationRule

class TestAppConfig(JSONConfig):
    """測試用應用配置類"""
    app_name: str = Field(default="test_app")
    debug: bool = Field(default=False)
    port: int = Field(default=8000)

class TestAIConfig(JSONConfig):
    """測試用 AI 配置類"""
    model: str = Field(default="gpt-3.5-turbo")
    temperature: float = Field(default=0.7)
    max_tokens: int = Field(default=2000)

@pytest.fixture
def temp_config_dir():
    """創建臨時配置目錄"""
    with tempfile.TemporaryDirectory() as temp_dir:
        yield Path(temp_dir)

@pytest.fixture
def config_manager(temp_config_dir):
    """創建配置管理器實例"""
    return ConfigManager(temp_config_dir)

def test_register_multiple_configs(config_manager):
    """測試註冊多個配置"""
    # 註冊應用配置
    app_config = config_manager.register_config(
        name="app",
        config_class=TestAppConfig,
        filename="app.json"
    )
    assert isinstance(app_config, TestAppConfig)
    
    # 註冊 AI 配置
    ai_config = config_manager.register_config(
        name="ai",
        config_class=TestAIConfig,
        filename="ai.json"
    )
    assert isinstance(ai_config, TestAIConfig)
    
    # 驗證配置文件創建
    assert (config_manager.base_path / "app.json").exists()
    assert (config_manager.base_path / "ai.json").exists()

def test_config_validation_integration(config_manager):
    """測試配置驗證整合"""
    # 創建驗證器
    validator = ConfigValidator()
    validator.add_rule(
        ValidationRule("port")
        .required()
        .min_value(1024)
        .max_value(65535)
    )
    
    # 註冊帶驗證器的配置
    config = config_manager.register_config(
        name="app",
        config_class=TestAppConfig,
        filename="app.json",
        validator=validator
    )
    
    # 測試有效更新
    assert config_manager.update_config("app", {"port": 8080})
    
    # 測試無效更新
    with pytest.raises(ValueError):
        config_manager.update_config("app", {"port": 80})

def test_config_reloading(config_manager):
    """測試配置重新加載"""
    # 註冊配置
    config = config_manager.register_config(
        name="app",
        config_class=TestAppConfig,
        filename="app.json"
    )
    
    # 修改配置文件
    config_path = config_manager.base_path / "app.json"
    with open(config_path, 'w') as f:
        json.dump({
            "app_name": "modified_app",
            "port": 9000
        }, f)
    
    # 重新加載單個配置
    assert config_manager.reload_config("app")
    reloaded_config = config_manager.get_config("app")
    assert reloaded_config.app_name == "modified_app"
    assert reloaded_config.port == 9000
    
    # 重新加載所有配置
    assert config_manager.reload_all()

def test_config_error_handling(config_manager):
    """測試錯誤處理"""
    # 測試獲取不存在的配置
    with pytest.raises(KeyError):
        config_manager.get_config("nonexistent")
    
    # 測試更新不存在的配置
    with pytest.raises(KeyError):
        config_manager.update_config("nonexistent", {})
    
    # 測試重新加載不存在的配置
    with pytest.raises(KeyError):
        config_manager.reload_config("nonexistent")

def test_config_save_operations(config_manager):
    """測試配置保存操作"""
    # 註冊多個配置
    app_config = config_manager.register_config(
        name="app",
        config_class=TestAppConfig,
        filename="app.json"
    )
    ai_config = config_manager.register_config(
        name="ai",
        config_class=TestAIConfig,
        filename="ai.json"
    )
    
    # 修改配置
    app_config.app_name = "modified_app"
    ai_config.temperature = 0.8
    
    # 保存單個配置
    assert config_manager.save_config("app")
    
    # 保存所有配置
    assert config_manager.save_all()
    
    # 驗證保存的內容
    app_data = json.loads((config_manager.base_path / "app.json").read_text())
    assert app_data["app_name"] == "modified_app"
    
    ai_data = json.loads((config_manager.base_path / "ai.json").read_text())
    assert ai_data["temperature"] == 0.8

def test_config_type_handling(config_manager):
    """測試配置類型處理"""
    # 註冊配置
    config = config_manager.register_config(
        name="app",
        config_class=TestAppConfig,
        filename="app.json"
    )
    
    # 測試不同類型的更新
    updates = {
        "app_name": "new_app",  # 字符串
        "debug": True,  # 布爾值
        "port": 9000  # 整數
    }
    
    assert config_manager.update_config("app", updates)
    
    # 驗證類型正確性
    config = config_manager.get_config("app")
    assert isinstance(config.app_name, str)
    assert isinstance(config.debug, bool)
    assert isinstance(config.port, int)

def test_config_inheritance(config_manager):
    """測試配置繼承"""
    class ExtendedConfig(TestAppConfig):
        api_key: Optional[str] = Field(default=None)
        rate_limit: int = Field(default=100)
    
    # 註冊擴展配置
    config = config_manager.register_config(
        name="extended",
        config_class=ExtendedConfig,
        filename="extended.json"
    )
    
    # 驗證繼承的字段
    assert config.app_name == "test_app"  # 從父類繼承的默認值
    assert config.api_key is None  # 新增字段
    assert config.rate_limit == 100  # 新增字段

def test_config_manager_initialization(temp_config_dir):
    """測試配置管理器初始化"""
    # 測試有效路徑
    manager = ConfigManager(temp_config_dir)
    assert manager.base_path == temp_config_dir
    assert manager.base_path.exists()
    
    # 測試創建新目錄
    new_dir = temp_config_dir / "nested" / "config"
    manager = ConfigManager(new_dir)
    assert new_dir.exists()

def test_validator_integration(config_manager):
    """測試驗證器整合"""
    # 創建複雜的驗證規則
    validator = ConfigValidator()
    validator.add_rule(
        ValidationRule("app_name")
        .required()
        .min_length(3)
        .max_length(50)
    )
    validator.add_rule(
        ValidationRule("port")
        .required()
        .min_value(1024)
        .max_value(65535)
    )
    
    # 註冊帶驗證器的配置
    config = config_manager.register_config(
        name="app",
        config_class=TestAppConfig,
        filename="app.json",
        validator=validator
    )
    
    # 測試多重驗證失敗
    with pytest.raises(ValueError) as exc:
        config_manager.update_config("app", {
            "app_name": "a",  # 太短
            "port": 80  # 太小
        })
    
    # 驗證錯誤消息包含所有失敗的規則
    error_msg = str(exc.value)
    assert "app_name" in error_msg
    assert "port" in error_msg 