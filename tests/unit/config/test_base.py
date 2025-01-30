import pytest
import os
from pathlib import Path
from typing import Dict, List, Optional
from pydantic import Field, ConfigDict
from src.shared.config.base import BaseConfig, ConfigError

class TestConfig(BaseConfig):
    """測試用配置類"""
    api_key: str = Field(default="default_key", description="API金鑰")
    port: int = Field(default=8000, description="服務端口")
    debug: bool = Field(default=False, description="調試模式")
    data_path: Optional[Path] = Field(default=None, description="數據路徑")
    tags: List[str] = Field(default_factory=list, description="標籤列表")
    settings: Dict[str, str] = Field(default_factory=dict, description="設置字典")

    model_config = ConfigDict(
        validate_assignment=True,
        extra="allow"
    )

    def _load_config(self) -> None:
        """測試用載入配置方法，不加載任何配置文件"""
        pass

    def save(self) -> bool:
        """測試用保存配置方法"""
        return True

def test_init_with_data():
    """測試使用數據初始化"""
    data = {
        "api_key": "test_key",
        "port": 9000,
        "debug": False,
        "data_path": None,
        "tags": [],
        "settings": {}
    }
    config = TestConfig(**data)
    
    # 驗證初始化後的值
    assert config.api_key == "test_key"
    assert config.port == 9000
    assert config.debug is False
    assert config.data_path is None
    assert isinstance(config.tags, list)
    assert len(config.tags) == 0
    assert isinstance(config.settings, dict)
    assert len(config.settings) == 0

def test_env_vars(monkeypatch):
    """測試環境變量加載"""
    # 清理可能影響的環境變量
    for key in ["API_KEY", "PORT", "DEBUG", "DATA_PATH", "TAGS", "SETTINGS"]:
        monkeypatch.delenv(key, raising=False)
    
    # 設置新的環境變量
    monkeypatch.setenv("API_KEY", "env_key")
    monkeypatch.setenv("PORT", "9000")
    monkeypatch.setenv("DEBUG", "true")
    monkeypatch.setenv("DATA_PATH", str(Path("/test/path")))
    monkeypatch.setenv("TAGS", '["tag1","tag2","tag3"]')  # 使用 JSON 格式
    monkeypatch.setenv("SETTINGS", '{"key":"value"}')
    
    config = TestConfig()
    
    assert config.api_key == "env_key"
    assert config.port == 9000
    assert config.debug is True
    assert str(config.data_path) == str(Path("/test/path"))
    assert config.tags == ["tag1", "tag2", "tag3"]
    assert config.settings == {"key": "value"}

def test_env_vars_with_prefix(monkeypatch):
    """測試帶前綴的環境變量加載"""
    class PrefixConfig(TestConfig):
        model_config = ConfigDict(
            env_prefix="TEST_",
            env_nested_delimiter="__",
            validate_assignment=True,
            extra="allow",
            json_schema_extra={"env_file": None}
        )
    
    # 清理可能影響的環境變量
    for key in ["TEST_API_KEY", "TEST_PORT"]:
        monkeypatch.delenv(key, raising=False)
    
    monkeypatch.setenv("TEST_API_KEY", "prefix_key")
    monkeypatch.setenv("TEST_PORT", "9001")
    
    config = PrefixConfig()
    
    assert config.api_key == "prefix_key"
    assert config.port == 9001

def test_env_vars_nested(monkeypatch):
    """測試嵌套環境變量加載"""
    # 清理可能影響的環境變量
    for key in ["SETTINGS__DATABASE", "SETTINGS__HOST"]:
        monkeypatch.delenv(key, raising=False)
    
    monkeypatch.setenv("SETTINGS__DATABASE", "mysql")
    monkeypatch.setenv("SETTINGS__HOST", "localhost")
    
    config = TestConfig()
    
    assert isinstance(config.settings, dict)
    assert config.settings == {
        "database": "mysql",
        "host": "localhost"
    }

def test_get_config_value():
    """測試獲取配置值"""
    config = TestConfig(api_key="test_key")
    assert config.get("api_key") == "test_key"
    assert config.get("nonexistent", "default") == "default"

def test_set_config_value():
    """測試設置配置值"""
    config = TestConfig()
    config.set("api_key", "new_key")
    assert config.api_key == "new_key"

def test_update_config():
    """測試更新配置"""
    config = TestConfig()
    new_data = {
        "api_key": "updated_key",
        "port": 9002
    }
    assert config.update(new_data) is True
    assert config.api_key == "updated_key"
    assert config.port == 9002

def test_to_dict():
    """測試轉換為字典"""
    config = TestConfig(api_key="test_key", port=9003)
    data = config.to_dict()
    assert data["api_key"] == "test_key"
    assert data["port"] == 9003

def test_get_fields():
    """測試獲取字段信息"""
    config = TestConfig()
    fields = config.get_fields()
    assert "api_key" in fields
    assert "port" in fields
    assert "debug" in fields

@pytest.fixture
def config_data():
    return {
        "app": {
            "name": "test_app",
            "version": "1.0.0",
            "debug": True
        },
        "database": {
            "url": "sqlite:///test.db",
            "echo": False
        },
        "line": {
            "channel_secret": "test_secret",
            "channel_access_token": "test_token"
        }
    }

@pytest.fixture
def config_file(tmp_path, config_data):
    import json
    config_path = tmp_path / "config.json"
    with open(config_path, "w") as f:
        json.dump(config_data, f)
    return config_path

def test_load_config_from_file(config_file, config_data):
    """測試從文件加載配置"""
    config = BaseConfig()
    config.load_file(config_file)
    
    assert config.get("app.name") == config_data["app"]["name"]
    assert config.get("database.url") == config_data["database"]["url"]
    assert config.get("line.channel_secret") == config_data["line"]["channel_secret"]

def test_load_config_from_dict(config_data):
    """測試從字典加載配置"""
    config = BaseConfig()
    config.load_dict(config_data)
    
    assert config.get("app.name") == config_data["app"]["name"]
    assert config.get("database.url") == config_data["database"]["url"]

def test_get_nested_config():
    """測試獲取嵌套配置"""
    config = BaseConfig()
    config.load_dict({
        "a": {
            "b": {
                "c": "value"
            }
        }
    })
    
    assert config.get("a.b.c") == "value"
    assert config.get("a.b") == {"c": "value"}
    assert config.get("a") == {"b": {"c": "value"}}

def test_get_default_value():
    """測試獲取默認值"""
    config = BaseConfig()
    
    assert config.get("non.existent.key", default="default") == "default"
    assert config.get("non.existent.key", default=123) == 123

def test_config_validation():
    """測試配置驗證"""
    config = BaseConfig()
    
    # 測試無效的鍵名
    with pytest.raises(ConfigError):
        config.set("", "value")
    
    with pytest.raises(ConfigError):
        config.set(".", "value")
    
    with pytest.raises(ConfigError):
        config.set("invalid.", "value")

def test_config_merge():
    """測試配置合併"""
    config = BaseConfig()
    
    # 初始配置
    config.load_dict({
        "a": {
            "b": 1,
            "c": 2
        },
        "d": 3
    })
    
    # 合併新配置
    config.merge({
        "a": {
            "b": 10,
            "d": 4
        },
        "e": 5
    })
    
    assert config.get("a.b") == 10  # 被覆蓋
    assert config.get("a.c") == 2   # 保持不變
    assert config.get("a.d") == 4   # 新增
    assert config.get("d") == 3     # 保持不變
    assert config.get("e") == 5     # 新增

def test_config_to_dict():
    """測試配置轉換為字典"""
    original_data = {
        "app": {
            "name": "test",
            "version": "1.0"
        },
        "settings": {
            "debug": True
        }
    }
    
    config = BaseConfig()
    config.load_dict(original_data)
    
    result = config.to_dict()
    assert result == original_data

def test_environment_override():
    """測試環境變量覆蓋"""
    import os
    
    config = BaseConfig()
    config.load_dict({
        "database": {
            "url": "default_url",
            "port": 5432
        }
    })
    
    # 設置環境變量
    os.environ["TEST_DATABASE_URL"] = "env_url"
    os.environ["TEST_DATABASE_PORT"] = "5433"
    
    # 從環境變量加載
    config.load_env(prefix="TEST_")
    
    assert config.get("database.url") == "env_url"
    assert config.get("database.port") == 5433
    
    # 清理環境變量
    del os.environ["TEST_DATABASE_URL"]
    del os.environ["TEST_DATABASE_PORT"] 