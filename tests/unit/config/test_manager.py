import pytest
from pathlib import Path
import tempfile
import json
from typing import Dict, Optional
from src.shared.config.manager import ConfigManager
from src.shared.config.json_config import JSONConfig
from src.shared.config.validator import ConfigValidator, ValidationRule
from src.shared.config.base import ConfigError

class TestConfig(JSONConfig):
    """測試用配置類"""
    api_key: str = None
    port: int = 8000
    debug: bool = False

@pytest.fixture
def temp_config_dir(tmp_path):
    """創建臨時配置目錄"""
    config_dir = tmp_path / "config"
    config_dir.mkdir(parents=True, exist_ok=True)
    return config_dir

@pytest.fixture
def config_manager(temp_config_dir):
    """創建配置管理器實例"""
    return ConfigManager(temp_config_dir)

@pytest.fixture
def validator():
    """創建配置驗證器"""
    validator = ConfigValidator()
    validator.add_rule(
        ValidationRule("port")
        .required()
        .min_value(1024)
        .max_value(65535)
    )
    return validator

def test_init_config_manager(temp_config_dir):
    """測試配置管理器初始化"""
    manager = ConfigManager(temp_config_dir)
    assert manager.base_path == temp_config_dir
    assert isinstance(manager.configs, dict)
    assert isinstance(manager.validators, dict)
    assert temp_config_dir.exists()

def test_register_config(config_manager):
    """測試註冊配置"""
    config = config_manager.register_config(
        name="test",
        config_class=TestConfig,
        filename="test.json"
    )
    
    assert isinstance(config, TestConfig)
    assert "test" in config_manager.configs
    assert config_manager.configs["test"] == config
    assert (config_manager.base_path / "test.json").exists()

def test_register_config_with_validator(config_manager):
    """測試使用驗證器註冊配置"""
    validator = ConfigValidator()
    validator.add_rule(
        ValidationRule("api_key")
        .required()
        .custom("API金鑰不能為空", lambda x: bool(x))
    )
    
    config = config_manager.register_config(
        name="test",
        config_class=TestConfig,
        filename="test.json",
        validator=validator
    )
    
    assert isinstance(config, TestConfig)
    assert "test" in config_manager.configs
    assert "test" in config_manager.validators
    assert config_manager.validators["test"] == validator

def test_get_config(config_manager):
    """測試獲取配置"""
    # 先註冊配置
    original_config = config_manager.register_config(
        name="test",
        config_class=TestConfig,
        filename="test.json"
    )
    
    # 獲取配置
    config = config_manager.get_config("test")
    assert config == original_config
    
    # 測試獲取不存在的配置
    with pytest.raises(KeyError):
        config_manager.get_config("nonexistent")

def test_validate_config(config_manager):
    """測試配置驗證"""
    # 創建驗證器
    validator = ConfigValidator()
    validator.add_rule(
        ValidationRule("api_key")
        .required()
        .custom(lambda x: x is not None and len(str(x)) > 0, "API金鑰不能為空")
    )
    
    # 註冊配置
    config = config_manager.register_config(
        name="test",
        config_class=TestConfig,
        filename="test.json",
        validator=validator
    )
    
    # 測試驗證失敗
    with pytest.raises(ValueError) as exc_info:
        config_manager.validate_config("test")
    assert "API金鑰不能為空" in str(exc_info.value)
    
    # 設置有效值
    config.api_key = "test_key"
    assert config_manager.validate_config("test") is True

def test_reload_config(config_manager):
    """測試重新載入配置"""
    # 註冊配置
    config = config_manager.register_config(
        name="test",
        config_class=TestConfig,
        filename="test.json"
    )
    
    # 修改並保存配置
    config.api_key = "test_key"
    config.save()
    
    # 重新載入
    reloaded = config_manager.reload_config("test")
    assert reloaded is True
    assert config_manager.get_config("test").api_key == "test_key"
    
    # 測試重新載入不存在的配置
    with pytest.raises(KeyError):
        config_manager.reload_config("nonexistent")

def test_update_config(config_manager):
    """測試更新配置"""
    # 註冊配置
    config = config_manager.register_config(
        name="test",
        config_class=TestConfig,
        filename="test_config.json"
    )
    
    # 更新配置
    update_data = {
        "api_key": "updated_key",
        "port": 9000
    }
    assert config_manager.update_config("test", update_data)
    
    # 驗證更新
    updated = config_manager.get_config("test")
    assert updated.api_key == "updated_key"
    assert updated.port == 9000
    
    # 測試更新不存在的配置
    with pytest.raises(KeyError):
        config_manager.update_config("nonexistent", update_data)

def test_save_and_reload(config_manager):
    """測試保存和重新加載配置"""
    # 註冊並更新配置
    config = config_manager.register_config(
        name="test",
        config_class=TestConfig,
        filename="test_config.json"
    )
    config_manager.update_config("test", {
        "api_key": "saved_key",
        "port": 9000
    })
    
    # 保存所有配置
    assert config_manager.save_all()
    
    # 創建新的管理器實例
    new_manager = ConfigManager(config_manager.base_path)
    new_manager.register_config(
        name="test",
        config_class=TestConfig,
        filename="test_config.json"
    )
    
    # 驗證加載的配置
    loaded = new_manager.get_config("test")
    assert loaded.api_key == "saved_key"
    assert loaded.port == 9000

def test_multiple_configs(config_manager):
    """測試多個配置"""
    # 註冊多個配置
    config1 = config_manager.register_config(
        name="app1",
        config_class=TestConfig,
        filename="app1.json"
    )
    config2 = config_manager.register_config(
        name="app2",
        config_class=TestConfig,
        filename="app2.json"
    )
    
    # 更新不同配置
    config_manager.update_config("app1", {"api_key": "key1"})
    config_manager.update_config("app2", {"api_key": "key2"})
    
    # 驗證各自的更新
    assert config_manager.get_config("app1").api_key == "key1"
    assert config_manager.get_config("app2").api_key == "key2"
    
    # 保存並重新加載
    assert config_manager.save_all()
    config_manager.reload_all()
    
    # 驗證重新加載後的值
    assert config_manager.get_config("app1").api_key == "key1"
    assert config_manager.get_config("app2").api_key == "key2"

def teardown_module(module):
    """清理測試文件"""
    # 清理可能存在的測試文件
    temp_dir = Path(tempfile.gettempdir())
    for pattern in ['*.json']:
        for file in temp_dir.glob(pattern):
            try:
                file.unlink()
            except OSError:
                pass

@pytest.fixture
def config_dir(tmp_path):
    """創建測試配置目錄"""
    config_dir = tmp_path / "config"
    config_dir.mkdir()
    return config_dir

@pytest.fixture
def config_files(config_dir):
    """創建測試配置文件"""
    # 創建基礎配置
    base_config = {
        "app": {
            "name": "test_app",
            "version": "1.0.0"
        },
        "database": {
            "url": "sqlite:///test.db"
        }
    }
    
    # 創建開發環境配置
    dev_config = {
        "app": {
            "debug": True
        },
        "database": {
            "echo": True
        }
    }
    
    # 創建生產環境配置
    prod_config = {
        "app": {
            "debug": False
        },
        "database": {
            "url": "postgresql://user:pass@localhost/prod"
        }
    }
    
    # 寫入配置文件
    with open(config_dir / "base.json", "w") as f:
        json.dump(base_config, f)
    
    with open(config_dir / "development.json", "w") as f:
        json.dump(dev_config, f)
    
    with open(config_dir / "production.json", "w") as f:
        json.dump(prod_config, f)
    
    return {
        "base": base_config,
        "development": dev_config,
        "production": prod_config
    }

def test_load_config_files(config_dir, config_files):
    """測試加載配置文件"""
    manager = ConfigManager(config_dir=str(config_dir))
    
    # 加載開發環境配置
    manager.load_config("development")
    config = manager.get_config()
    
    # 驗證基礎配置和環境配置的合併
    assert config.get("app.name") == config_files["base"]["app"]["name"]
    assert config.get("app.debug") == config_files["development"]["app"]["debug"]
    assert config.get("database.url") == config_files["base"]["database"]["url"]
    assert config.get("database.echo") == config_files["development"]["database"]["echo"]

def test_environment_override(config_dir, config_files):
    """測試環境變量覆蓋配置"""
    import os
    
    manager = ConfigManager(config_dir=str(config_dir))
    
    # 設置環境變量
    os.environ["TEST_APP_NAME"] = "env_app"
    os.environ["TEST_DATABASE_URL"] = "sqlite:///env.db"
    
    # 加載配置並應用環境變量
    manager.load_config("development", env_prefix="TEST_")
    config = manager.get_config()
    
    # 驗證環境變量覆蓋
    assert config.get("app.name") == "env_app"
    assert config.get("database.url") == "sqlite:///env.db"
    
    # 清理環境變量
    del os.environ["TEST_APP_NAME"]
    del os.environ["TEST_DATABASE_URL"]

def test_invalid_environment(config_dir):
    """測試無效的環境名稱"""
    manager = ConfigManager(config_dir=str(config_dir))
    
    with pytest.raises(ConfigError):
        manager.load_config("invalid_env")

def test_missing_base_config(tmp_path):
    """測試缺少基礎配置文件"""
    config_dir = tmp_path / "empty_config"
    config_dir.mkdir()
    
    manager = ConfigManager(config_dir=str(config_dir))
    
    with pytest.raises(ConfigError):
        manager.load_config("development")

def test_get_environment(config_dir, config_files):
    """測試獲取當前環境"""
    manager = ConfigManager(config_dir=str(config_dir))
    
    # 加載開發環境配置
    manager.load_config("development")
    assert manager.get_environment() == "development"
    
    # 加載生產環境配置
    manager.load_config("production")
    assert manager.get_environment() == "production"

def test_reload_config(config_dir, config_files):
    """測試重新加載配置"""
    manager = ConfigManager(config_dir=str(config_dir))
    manager.load_config("development")
    
    # 修改配置文件
    import json
    dev_config = {
        "app": {
            "debug": False,
            "new_setting": "value"
        }
    }
    with open(config_dir / "development.json", "w") as f:
        json.dump(dev_config, f)
    
    # 重新加載配置
    manager.reload_config()
    config = manager.get_config()
    
    # 驗證新配置
    assert config.get("app.debug") is False
    assert config.get("app.new_setting") == "value"

def test_validate_config_schema(config_dir):
    """測試配置模式驗證"""
    from pydantic import BaseModel
    
    class AppConfig(BaseModel):
        name: str
        debug: bool = False
    
    class DatabaseConfig(BaseModel):
        url: str
        echo: bool = False
    
    class Config(BaseModel):
        app: AppConfig
        database: DatabaseConfig
    
    manager = ConfigManager(config_dir=str(config_dir))
    
    # 創建有效的配置
    import json
    valid_config = {
        "app": {
            "name": "test_app",
            "debug": True
        },
        "database": {
            "url": "sqlite:///test.db",
            "echo": True
        }
    }
    with open(config_dir / "valid.json", "w") as f:
        json.dump(valid_config, f)
    
    # 加載並驗證配置
    manager.load_config("valid", schema=Config)
    
    # 創建無效的配置
    invalid_config = {
        "app": {
            "debug": True  # 缺少必需的 name 字段
        },
        "database": {
            "url": "sqlite:///test.db"
        }
    }
    with open(config_dir / "invalid.json", "w") as f:
        json.dump(invalid_config, f)
    
    # 應該拋出驗證錯誤
    with pytest.raises(Exception):
        manager.load_config("invalid", schema=Config) 