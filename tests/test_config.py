import pytest
import os
from src.shared.config.base import ConfigManager, ConfigError
from pydantic import BaseModel

class TestConfigManager:
    class TestConfig(BaseModel):
        test_var: str

    @pytest.fixture(autouse=True)
    def setup_method(self):
        """每個測試方法前執行的設置"""
        # 設置測試環境變量
        os.environ["TEST_VAR"] = "test_value"
        os.environ["LINE_CHANNEL_SECRET"] = "test_secret"
        os.environ["LINE_CHANNEL_ACCESS_TOKEN"] = "test_token"
        
        # 重置 ConfigManager 單例
        ConfigManager._instance = None
        
    def test_load_config(self):
        """測試配置加載"""
        config = ConfigManager()
        config.set("TEST_VAR", os.getenv("TEST_VAR"))
        result = config.load()
        
        assert result is not None
        assert isinstance(result, dict)
        assert result["TEST_VAR"] == "test_value"
        
    def test_get_config(self):
        """測試獲取配置值"""
        config = ConfigManager()
        config.set("TEST_KEY", "test_value")
        
        assert config.get("TEST_KEY") == "test_value"
        assert config.get("NON_EXISTENT", "default") == "default"
        
    def test_set_config(self):
        """測試設置配置值"""
        config = ConfigManager()
        config.set("NEW_KEY", "new_value")
        
        assert config.get("NEW_KEY") == "new_value"
        
    def test_validate_config(self):
        """測試配置驗證"""
        config = ConfigManager()
        
        # 測試有效配置
        config.set("TEST_VAR", "valid_value")
        assert config.get("TEST_VAR") == "valid_value"
        
        # 測試無效配置
        with pytest.raises(ValueError):
            test_config = self.TestConfig(test_var=None)
        
    def test_env_variables(self):
        """測試環境變量處理"""
        config = ConfigManager()
        
        # 設置環境變量
        config.set("LINE_CHANNEL_SECRET", os.getenv("LINE_CHANNEL_SECRET"))
        config.set("LINE_CHANNEL_ACCESS_TOKEN", os.getenv("LINE_CHANNEL_ACCESS_TOKEN"))
        
        # 測試必需的環境變量
        assert config.get("LINE_CHANNEL_SECRET") == "test_secret"
        assert config.get("LINE_CHANNEL_ACCESS_TOKEN") == "test_token"
        
    def test_sync_operations(self):
        """測試同步操作"""
        config = ConfigManager()
        
        # 測試加載
        config.set("TEST_KEY", "test_value")
        result = config.load()
        
        assert result is not None
        assert isinstance(result, dict)
        assert "TEST_KEY" in result
        assert result["TEST_KEY"] == "test_value"
        
    def test_config_validation(self):
        """測試配置驗證邏輯"""
        config = ConfigManager()
        
        # 測試基本類型
        config.set("int_value", 42)
        config.set("str_value", "test")
        config.set("bool_value", True)
        
        assert config.get("int_value") == 42
        assert config.get("str_value") == "test"
        assert config.get("bool_value") is True
        
    def test_nested_config(self):
        """測試嵌套配置"""
        config = ConfigManager()
        
        # 設置嵌套配置
        nested_config = {
            "database": {
                "host": "localhost",
                "port": 5432,
                "credentials": {
                    "username": "test",
                    "password": "secret"
                }
            }
        }
        
        config.set("nested", nested_config)
        result = config.get("nested")
        
        assert result == nested_config
        assert result["database"]["port"] == 5432
        
    def test_config_merge(self):
        """測試配置合併"""
        config = ConfigManager()
        
        # 初始配置
        config.set("settings", {
            "debug": True,
            "timeout": 30
        })
        
        # 合併新配置
        new_settings = {
            "timeout": 60,
            "retry": 3
        }
        
        config.set("settings", new_settings)
        result = config.get("settings")
        
        assert result["timeout"] == 60
        assert result["retry"] == 3
        
    def test_deep_merge(self):
        """測試深度合併配置"""
        config = ConfigManager()
        
        # 初始配置
        initial = {
            "database": {
                "host": "localhost",
                "port": 5432,
                "settings": {
                    "pool_size": 5,
                    "timeout": 30
                }
            }
        }
        config.set("config", initial)
        
        # 合併配置
        update = {
            "database": {
                "port": 5433,
                "settings": {
                    "timeout": 60,
                    "max_connections": 10
                }
            }
        }
        config.set("config", update)
        
        result = config.get("config")
        assert result["database"]["port"] == 5433
        assert result["database"]["settings"]["timeout"] == 60
        assert result["database"]["settings"]["max_connections"] == 10
        
    def test_error_handling(self):
        """測試錯誤處理"""
        config = ConfigManager()
        
        # 測試無效的鍵
        with pytest.raises(ValueError):
            config.set("", "value")
            
        # 測試無效的鍵
        with pytest.raises(TypeError):
            config.set(None, "value")
            
        # 測試不存在的鍵
        assert config.get("non.existent.key") is None
        
    def test_config_validation_advanced(self):
        """測試進階配置驗證"""
        config = ConfigManager()
        
        # 測試數據類型轉換
        test_cases = [
            ("int_val", "123", 123),
            ("float_val", "3.14", 3.14),
            ("bool_val", "true", True),
            ("bool_val2", "yes", True),
            ("bool_val3", "1", True),
            ("bool_val4", "false", False),
            ("bool_val5", "no", False),
            ("bool_val6", "0", False),
            ("str_val", "test", "test"),
            ("list_val", "[1,2,3]", [1,2,3]),
            ("dict_val", '{"key":"value"}', {"key": "value"})
        ]
        
        for key, input_val, expected in test_cases:
            config.set(key, input_val)
            result = config.get(key)
            assert result == expected, f"Failed for key: {key}, input: {input_val}, expected: {expected}, got: {result}"
            
    def test_environment_override(self):
        """測試環境變量覆蓋"""
        config = ConfigManager()
        
        # 設置默認值
        config.set("DATABASE_URL", "default_url")
        
        # 設置環境變量
        os.environ["DATABASE_URL"] = "env_url"
        
        # 重新加載配置
        config.set("DATABASE_URL", os.getenv("DATABASE_URL"))
        
        assert config.get("DATABASE_URL") == "env_url"
        
    def test_singleton_behavior(self):
        """測試單例模式行為"""
        config1 = ConfigManager()
        config2 = ConfigManager()
        
        config1.set("test_key", "test_value")
        assert config2.get("test_key") == "test_value"
        
        config2.set("another_key", "another_value")
        assert config1.get("another_key") == "another_value"
        
        assert id(config1) == id(config2)
        
    def test_config_persistence(self):
        """測試配置持久性"""
        config = ConfigManager()
        
        # 設置多個配置值
        test_data = {
            "str_value": "test",
            "int_value": 42,
            "nested": {
                "key": "value"
            }
        }
        
        for key, value in test_data.items():
            config.set(key, value)
            
        # 驗證所有值都被正確保存
        result = config.load()
        assert result is not None
        for key, value in test_data.items():
            assert config.get(key) == value
            
    def teardown_method(self):
        """每個測試方法後執行的清理"""
        # 清理環境變量
        for key in ["TEST_VAR", "LINE_CHANNEL_SECRET", "LINE_CHANNEL_ACCESS_TOKEN", "DATABASE_URL"]:
            if key in os.environ:
                del os.environ[key] 

    def test_config_validation_extended(self):
        """擴展配置驗證測試"""
        config = ConfigManager()
        
        # 測試必要字段
        with pytest.raises(ValueError):
            config.validate({
                "database": {},  # 缺少必要字段
                "line": {}
            })
            
        # 測試類型驗證
        with pytest.raises(TypeError):
            config.validate({
                "database": {
                    "port": "not_a_number"  # 錯誤類型
                }
            })
            
        # 測試嵌套配置
        valid_config = {
            "database": {
                "url": "sqlite:///:memory:",
                "pool_size": 5
            },
            "line": {
                "channel_secret": "test_secret",
                "channel_token": "test_token"
            }
        }
        assert config.validate(valid_config) is True 