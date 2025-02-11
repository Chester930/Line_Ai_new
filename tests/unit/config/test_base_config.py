import pytest
from pathlib import Path
from typing import Dict, Optional, Any
from pydantic import BaseModel, Field, ConfigDict
from src.shared.config.base import BaseConfig
import os

class TestBaseConfig(BaseConfig):
    """測試用基礎配置類"""
    app_name: str = Field(default="test_app")
    debug: bool = Field(default=False)
    port: int = Field(default=8000, gt=0)
    data_path: Optional[Path] = Field(default=None)
    settings: Dict[str, Any] = Field(default_factory=dict)
    
    model_config = ConfigDict(
        arbitrary_types_allowed=True,
        validate_assignment=True,
        extra='allow'
    )
    
    def __init__(self, **data):
        super().__init__(**data)
        self._config = self.model_dump()  # 初始化時保存配置到 _config
    
    def get(self, key: str, default: Any = None) -> Any:
        """獲取配置值"""
        try:
            # 先嘗試從實例屬性獲取
            if not key.startswith("settings."):
                if hasattr(self, key):
                    return getattr(self, key)
            
            # 處理嵌套路徑
            keys = key.split('.')
            current = self._config
            
            for k in keys:
                if not isinstance(current, dict) or k not in current:
                    return default
                current = current[k]
            return current
            
        except Exception:
            return default
    
    def set(self, key: str, value: Any) -> bool:
        """設置配置值"""
        try:
            # 處理嵌套路徑
            keys = key.split('.')
            
            # 如果是單層鍵，直接設置
            if len(keys) == 1:
                setattr(self, key, value)
                self._config[key] = value
                return True
            
            # 處理嵌套鍵
            current = self._config
            for k in keys[:-1]:
                if k not in current:
                    current[k] = {}
                current = current[k]
            
            # 設置最後一層的值
            current[keys[-1]] = value
            
            # 如果是 settings 下的配置，同步到 settings 屬性
            if keys[0] == "settings":
                self.settings = self._config["settings"]
            
            return True
            
        except Exception:
            return False
    
    def update(self, data: Dict[str, Any]) -> bool:
        """更新配置"""
        try:
            # 更新 _config
            self._config.update(data)
            
            # 更新實例屬性
            for key, value in data.items():
                if hasattr(self, key):
                    setattr(self, key, value)
            
            return True
        except Exception:
            return False

    def merge(self, other: 'TestBaseConfig') -> bool:
        """合併另一個配置"""
        if not isinstance(other, TestBaseConfig):
            raise ValueError("只能合併相同類型的配置")
            
        # 深度合併字典
        def deep_merge(d1: Dict[str, Any], d2: Dict[str, Any]) -> Dict[str, Any]:
            result = d1.copy()
            for key, value in d2.items():
                if key in result and isinstance(result[key], dict) and isinstance(value, dict):
                    result[key] = deep_merge(result[key], value)
                else:
                    result[key] = value
            return result
        
        try:
            # 獲取兩個配置的字典表示
            current = self.model_dump()
            other_data = other.model_dump()
            
            # 深度合併
            merged = deep_merge(current, other_data)
            
            # 更新當前配置
            for key, value in merged.items():
                if hasattr(self, key):
                    setattr(self, key, value)
            
            return True
        except Exception:
            return False
    
    def load_from_env(self, prefix: str = "") -> bool:
        """從環境變量加載配置"""
        try:
            for key, field in self.model_fields.items():
                env_key = f"{prefix}{key}".upper()
                if env_key in os.environ:
                    value = os.environ[env_key]
                    try:
                        # 根據字段類型轉換值
                        if field.annotation == bool:
                            value = value.lower() in ('true', '1', 'yes')
                        elif field.annotation == int:
                            value = int(value)
                        elif field.annotation == Path:
                            value = Path(value)
                        
                        setattr(self, key, value)
                    except (ValueError, TypeError):
                        continue  # 忽略轉換失敗的值
            return True
        except Exception:
            return False
    
    def load_from_dict(self, data: Dict[str, Any]) -> bool:
        """從字典加載配置"""
        try:
            # 驗證並更新
            validated = self.model_validate(data)
            for key, value in validated.model_dump().items():
                if hasattr(self, key):
                    setattr(self, key, value)
            return True
        except Exception as e:
            raise ValueError(f"無效的配置數據: {str(e)}")

@pytest.fixture
def config():
    return TestBaseConfig()

def test_env_variables():
    """測試環境變量處理"""
    # 設置環境變量
    os.environ["APP_NAME"] = "env_app"
    os.environ["DEBUG"] = "true"
    os.environ["PORT"] = "9000"
    
    try:
        config = TestBaseConfig()
        
        # 驗證環境變量是否正確加載
        assert config.app_name == "env_app"
        assert config.debug is True
        assert config.port == 9000
        
    finally:
        # 清理環境變量
        del os.environ["APP_NAME"]
        del os.environ["DEBUG"]
        del os.environ["PORT"]

def test_get_config_value(config):
    """測試獲取配置值"""
    # 確保 _config 已初始化
    assert config._config["app_name"] == "test_app"
    
    # 測試獲取實例屬性
    assert config.get("app_name") == "test_app"
    assert config.get("debug") is False
    
    # 測試獲取不存在的值
    assert config.get("nonexistent") is None
    assert config.get("nonexistent", "default") == "default"
    
    # 測試獲取嵌套配置
    config.settings = {"database": {"host": "localhost"}}
    config._config["settings"] = config.settings  # 同步到 _config
    assert config.get("settings.database.host") == "localhost"

def test_set_config_value(config):
    """測試設置配置值"""
    # 使用 set 方法設置值
    config.set("app_name", "new_app")
    assert config.get("app_name") == "new_app"
    
    # 直接設置屬性
    config.debug = True
    assert config.debug is True
    
    # 設置嵌套值
    config.set("settings.database.host", "localhost")
    assert config.get("settings.database.host") == "localhost"

def test_update_config(config):
    """測試更新配置"""
    # 使用 update 方法更新多個值
    update_data = {
        "app_name": "updated_app",
        "port": 9000,
        "custom_key": "custom_value"
    }
    
    assert config.update(update_data)
    assert config.get("app_name") == "updated_app"
    assert config.port == 9000
    assert config.get("custom_key") == "custom_value"

def test_to_dict(config):
    """測試轉換為字典"""
    # 設置一些值
    config.app_name = "test_app"
    config.debug = True
    config.settings = {"key": "value"}
    
    # 轉換為字典
    result = config.model_dump()
    
    assert isinstance(result, dict)
    assert result["app_name"] == "test_app"
    assert result["debug"] is True
    assert result["settings"]["key"] == "value"

def test_get_fields(config):
    """測試獲取字段信息"""
    fields = config.model_fields
    expected_fields = {"app_name", "debug", "port", "data_path", "settings"}
    
    # 檢查必要的字段是否存在
    for field in expected_fields:
        assert field in fields 

def test_base_config_advanced():
    """測試基礎配置類的進階功能"""
    original_env = os.environ.copy()
    
    try:
        # 清理環境變量
        for key in list(os.environ.keys()):
            if key.startswith("TEST_") or key in ["APP_NAME", "DEBUG", "PORT"]:
                del os.environ[key]
        
        config = TestBaseConfig()
        
        # 1. 配置驗證
        # 1.1 類型驗證
        with pytest.raises(ValueError):
            config.port = "invalid"
        
        with pytest.raises(ValueError):
            config.debug = "not_bool"
        
        # 1.2 值範圍驗證
        with pytest.raises(ValueError):
            config.port = -1
        
        # 2. 環境變量處理
        # 2.1 有效值處理
        os.environ["TEST_PORT"] = "9000"
        os.environ["TEST_DEBUG"] = "true"
        
        assert config.load_from_env("TEST_")
        assert config.port == 9000  # 先確認有效值被設置
        assert config.debug is True
        
        # 2.2 無效值處理
        os.environ["TEST_PORT"] = "invalid"
        assert config.load_from_env("TEST_")
        assert config.port == 9000  # 應該保持原值
        
        # 3. 配置合併
        other_config = TestBaseConfig(
            app_name="other_app",
            settings={"database": {"host": "localhost"}}
        )
        
        # 3.1 基本合併
        assert config.merge(other_config)
        assert config.app_name == "other_app"
        assert config.settings["database"]["host"] == "localhost"
        
        # 3.2 深度合併
        config.settings = {"api": {"version": "v1"}}
        other_config.settings = {"database": {"port": 5432}}
        
        assert config.merge(other_config)
        assert config.settings["api"]["version"] == "v1"
        assert config.settings["database"]["port"] == 5432
        
        # 4. 字典轉換
        data = {
            "app_name": "dict_app",
            "settings": {
                "api": {"key": "secret"}
            }
        }
        
        assert config.load_from_dict(data)
        assert config.app_name == "dict_app"
        assert config.settings["api"]["key"] == "secret"
        
        # 5. 錯誤處理
        with pytest.raises(ValueError):
            config.merge(None)
        
        with pytest.raises(ValueError):
            config.load_from_dict({"port": "invalid"})
        
    finally:
        # 恢復環境變量
        os.environ.clear()
        os.environ.update(original_env) 