import pytest
from src.shared.config.base import BaseConfig, ConfigField
from src.shared.config.json_config import JSONConfig
from pydantic import BaseModel
from typing import Optional, Dict, Any
import json
from pathlib import Path
import logging
from src.shared.config.manager import ConfigManager

logger = logging.getLogger(__name__)

class TestConfig(BaseConfig):
    """測試配置類"""
    app_name: str = "test_app"
    debug: bool = False
    port: int = 8000
    database_url: Optional[str] = None
    api_keys: Dict[str, str] = {}
    
    def _load_config(self) -> None:
        """載入配置"""
        try:
            if not self.config_path:
                self._config = self.model_dump(exclude={'config_path'})
                return
            
            if not self.config_path.exists():
                self.config_path.parent.mkdir(parents=True, exist_ok=True)
                self.config_path.write_text("{}")
            
            self._config = json.loads(self.config_path.read_text())
            logger.info(f"已載入配置: {self.config_path}")
            
            # 更新實例屬性
            for key, value in self._config.items():
                if hasattr(self, key):
                    setattr(self, key, value)
            
        except Exception as e:
            logger.error(f"載入配置失敗: {str(e)}")
            self._config = {}
    
    def save(self) -> bool:
        """保存配置"""
        try:
            if not self.config_path:
                return False
            
            # 合併實例屬性和配置字典
            data = self.model_dump(exclude={'config_path'})
            data.update(self._config)
            
            # 將 Path 對象轉換為字符串
            def convert_path(obj):
                if isinstance(obj, Path):
                    return str(obj)
                elif isinstance(obj, dict):
                    return {k: convert_path(v) for k, v in obj.items()}
                elif isinstance(obj, list):
                    return [convert_path(x) for x in obj]
                return obj
            
            data = convert_path(data)
            
            # 確保目標目錄存在
            if self.config_path:
                self.config_path.parent.mkdir(parents=True, exist_ok=True)
            
            self.config_path.write_text(
                json.dumps(data, indent=2, ensure_ascii=False)
            )
            logger.info(f"已保存配置: {self.config_path}")
            return True
            
        except Exception as e:
            logger.error(f"保存配置失敗: {str(e)}")
            return False

def test_config_creation():
    """測試配置創建"""
    config = TestConfig()
    assert config.app_name == "test_app"
    assert config.debug is False
    assert config.port == 8000
    assert config.database_url is None
    assert config.api_keys == {}

def test_config_from_dict():
    """測試從字典創建配置"""
    config_data = {
        "app_name": "my_app",
        "debug": True,
        "port": 9000,
        "database_url": "sqlite:///test.db",
        "api_keys": {"service1": "key1"}
    }
    config = TestConfig.model_validate(config_data)
    
    assert config.app_name == "my_app"
    assert config.debug is True
    assert config.port == 9000
    assert config.database_url == "sqlite:///test.db"
    assert config.api_keys == {"service1": "key1"}

def test_config_validation():
    """測試配置驗證"""
    with pytest.raises(ValueError):
        TestConfig.model_validate({
            "port": "invalid_port"  # 應該是整數
        })

def test_config_field():
    """測試配置字段"""
    field = ConfigField(
        name="test_field",
        type_=str,
        default="default_value",
        description="Test field description"
    )
    
    assert field.name == "test_field"
    assert field.type_ == str
    assert field.default == "default_value"
    assert field.description == "Test field description"

def test_config_to_dict():
    """測試配置轉換為字典"""
    config = TestConfig(
        app_name="test_app",
        debug=True,
        port=8000
    )
    config_dict = config.model_dump()
    
    assert isinstance(config_dict, dict)
    assert config_dict["app_name"] == "test_app"
    assert config_dict["debug"] is True
    assert config_dict["port"] == 8000

def test_config_update():
    """測試配置更新"""
    config = TestConfig()
    
    # 更新單個值
    config.app_name = "updated_app"
    assert config.app_name == "updated_app"
    
    # 更新多個值
    update_data = {
        "debug": True,
        "port": 9000
    }
    config = config.model_copy(update=update_data)
    
    assert config.debug is True
    assert config.port == 9000

def test_config_nested():
    """測試嵌套配置"""
    class DatabaseConfig(BaseModel):
        url: str
        port: int
        username: Optional[str] = None
    
    class NestedConfig(TestConfig):
        database: DatabaseConfig
        api_key: str
    
    config_data = {
        "database": {
            "url": "localhost",
            "port": 5432
        },
        "api_key": "test_key"
    }
    
    config = NestedConfig.model_validate(config_data)
    assert config.database.url == "localhost"
    assert config.database.port == 5432
    assert config.database.username is None
    assert config.api_key == "test_key"

def test_config_env_override():
    """測試環境變量覆蓋"""
    import os
    
    # 設置環境變量
    os.environ["TEST_APP_NAME"] = "env_app"
    os.environ["TEST_PORT"] = "9999"
    
    class EnvConfig(TestConfig):
        model_config = {
            "env_prefix": "TEST_",
            "validate_assignment": True,
            "extra": "allow"
        }
    
    config = EnvConfig()
    assert config.app_name == "env_app"
    assert config.port == 9999
    
    # 清理環境變量
    del os.environ["TEST_APP_NAME"]
    del os.environ["TEST_PORT"]

@pytest.fixture
def config_dir(tmp_path):
    return tmp_path / "config"

@pytest.fixture
def config_manager(config_dir):
    return ConfigManager(config_dir=config_dir)

class TestConfigManager:
    def test_environment_handling(self, config_manager, monkeypatch):
        monkeypatch.setenv("APP_ENV", "test")
        assert config_manager.get_environment() == "test"
        
        config_manager.set_environment("development")
        assert config_manager.environment == "development"
        
    def test_config_registration(self, config_manager):
        class TestConfig(BaseConfig):
            def __init__(self, **kwargs):
                super().__init__(**kwargs)
                self.data = {}
                
        config = config_manager.register_config(
            "test",
            TestConfig,
            filename="test.json"
        )
        assert config is not None
        assert "test" in config_manager.configs 

def test_config_file_operations(tmp_path):
    """測試配置文件操作"""
    config_dir = tmp_path / "config"
    config_dir.mkdir()
    
    # 創建測試配置
    config_data = {
        "app": {
            "name": "test_app",
            "debug": True
        },
        "database": {
            "url": "sqlite:///test.db"
        }
    }
    
    config_file = config_dir / "test.json"
    config_file.write_text(json.dumps(config_data))
    
    # 測試載入配置
    config = BaseConfig(config_path=str(config_file))
    assert config.get("app.name") == "test_app"
    assert config.get("database.url") == "sqlite:///test.db"
    
    # 測試保存配置
    config.set("app.version", "1.0.0")
    assert config.save()
    
    # 驗證保存的內容
    saved_data = json.loads(config_file.read_text())
    assert saved_data["app"]["version"] == "1.0.0" 