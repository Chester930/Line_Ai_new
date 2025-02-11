import pytest
import os
from pathlib import Path
from typing import Dict, List, Optional, Any
from pydantic import Field, ConfigDict, BaseModel, PrivateAttr, model_validator
from src.shared.config.base import BaseConfig, ConfigError

class TestConfig(BaseModel):
    """測試用配置類"""
    api_key: str = Field(default="default_key")
    port: int = Field(default=8000)
    debug: bool = Field(default=False)
    data_path: Optional[Path] = Field(default=None)
    tags: List[str] = Field(default_factory=list)
    settings: Dict[str, Any] = Field(default_factory=dict)

    # 使用 PrivateAttr 來定義私有屬性
    _data: Dict[str, Any] = PrivateAttr(default_factory=dict)
    _env_prefix: str = PrivateAttr(default="")

    model_config = ConfigDict(
        validate_assignment=True,
        extra='allow'
    )

    @model_validator(mode='before')
    @classmethod
    def pre_init(cls, data: Dict[str, Any]) -> Dict[str, Any]:
        """初始化前的處理"""
        # 保存環境變量前綴
        env_prefix = data.pop('env_prefix', '')
        
        # 處理初始數據
        init_data = data.pop('data', {})
        if init_data:
            data.update(init_data)
            
        # 加載環境變量
        for key, value in os.environ.items():
            if env_prefix and not key.startswith(env_prefix):
                continue
                
            clean_key = key[len(env_prefix):].lower()
            if clean_key == 'api_key':
                data['api_key'] = value
            elif clean_key == 'port':
                try:
                    data['port'] = int(value)
                except ValueError:
                    continue
            elif clean_key == 'debug':
                data['debug'] = value.lower() in ('true', '1', 'yes')
            elif clean_key.startswith('settings__'):
                parts = clean_key.split('__')[1:]
                settings = data.setdefault('settings', {})
                current = settings
                for part in parts[:-1]:
                    current = current.setdefault(part, {})
                current[parts[-1]] = value
        
        # 保存環境變量前綴供後續使用
        data['_env_prefix'] = env_prefix
        return data

    @model_validator(mode='after')
    def post_init(self) -> 'TestConfig':
        """初始化後的處理"""
        # 初始化內部數據
        self._data = {
            'api_key': self.api_key,
            'port': self.port,
            'debug': self.debug,
            'data_path': self.data_path,
            'tags': self.tags.copy(),
            'settings': self.settings.copy()
        }
        return self

    def get(self, key: str, default: Any = None) -> Any:
        """獲取配置值"""
        return getattr(self, key, default)

    def set(self, key: str, value: Any) -> None:
        """設置配置值"""
        object.__setattr__(self, key, value)
        self._data[key] = value

    def update(self, data: Dict[str, Any]) -> bool:
        """更新配置"""
        try:
            for key, value in data.items():
                if hasattr(self, key):
                    object.__setattr__(self, key, value)
                    self._data[key] = value
            return True
        except Exception:
            return False

    def to_dict(self, include_env: bool = True) -> Dict[str, Any]:
        """轉換為字典"""
        result = self._data.copy()
        
        if not include_env:
            return result
        
        # 添加環境變量
        for key, value in os.environ.items():
            if self._env_prefix and key.startswith(self._env_prefix):
                clean_key = key[len(self._env_prefix):].lower()
                if clean_key in result:
                    try:
                        if clean_key == 'port':
                            result[clean_key] = int(value)
                        elif clean_key == 'debug':
                            result[clean_key] = value.lower() in ('true', '1', 'yes')
                        else:
                            result[clean_key] = value
                    except ValueError:
                        continue
        
        return result

def test_init_with_data():
    """測試使用數據初始化"""
    config = TestConfig(data={
        "api_key": "test_key",
        "port": 9000,
        "debug": False
    })
    assert config.api_key == "test_key"
    assert config.port == 9000
    assert config.debug is False

def test_env_vars(monkeypatch):
    """測試環境變量加載"""
    monkeypatch.setenv("API_KEY", "env_key")
    monkeypatch.setenv("PORT", "9000")
    monkeypatch.setenv("DEBUG", "true")
    monkeypatch.setenv("SETTINGS__DATABASE", "mysql")
    monkeypatch.setenv("SETTINGS__HOST", "localhost")
    
    config = TestConfig()
    
    assert config.api_key == "env_key"
    assert config.port == 9000
    assert config.debug is True
    assert config.settings == {
        "database": "mysql",
        "host": "localhost"
    }

def test_env_vars_with_prefix(monkeypatch):
    """測試帶前綴的環境變量加載"""
    monkeypatch.setenv("TEST_API_KEY", "prefix_key")
    monkeypatch.setenv("TEST_PORT", "9001")
    
    config = TestConfig(env_prefix="TEST_")
    
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
    fields = config.model_fields
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

async def test_config_validation():
    """測試配置驗證"""
    config = BaseConfig()
    result = await config.validate()
    assert result is True

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
        "api_key": "test_key",
        "port": 9000,
        "settings": {
            "database": "test_db"
        }
    }
    config = TestConfig(**original_data)
    result = config.to_dict(include_env=False)
    
    assert result["api_key"] == original_data["api_key"]
    assert result["port"] == original_data["port"]
    assert result["settings"] == original_data["settings"]

def test_environment_override(monkeypatch):
    """測試環境變量覆蓋"""
    monkeypatch.setenv("TEST_API_KEY", "env_key")
    
    config = TestConfig(
        data={"api_key": "default_key"},
        env_prefix="TEST_"
    )
    
    assert config.api_key == "env_key"

@pytest.fixture
def temp_config_file(tmp_path):
    """創建臨時配置文件"""
    config_file = tmp_path / "test_config.json"
    config_file.write_text('{"test_key": "test_value"}')
    return config_file

def test_init_with_all_options(temp_config_file):
    """測試完整初始化選項"""
    config = BaseConfig(
        config_path=str(temp_config_file),
        env_prefix="TEST_",
        data={"key": "value"},
        name="test"
    )
    assert config._config_path == str(temp_config_file)
    assert config._env_prefix == "TEST_"
    assert config._data.get("key") == "value"
    assert config.name == "test"

def test_save_and_load(tmp_path):
    """測試保存和加載配置"""
    config_path = tmp_path / "save_test.json"
    config = BaseConfig(config_path=str(config_path))
    config.set("test_key", "test_value")
    
    assert config.save() is True
    assert config_path.exists()
    
    new_config = BaseConfig()
    assert new_config.load_file(config_path) is True
    assert new_config.get("test_key") == "test_value"

def test_error_handling():
    """測試錯誤處理"""
    config = BaseConfig()
    
    # 測試無效文件路徑
    assert config.load_file("nonexistent.json") is False
    
    # 測試無效的配置數據
    with pytest.raises(ConfigError):
        config.load_dict({"invalid": object()})
    
    # 測試無效的配置合併
    with pytest.raises(ConfigError):
        config.merge({"invalid": object()})

def test_validation_edge_cases():
    """測試驗證邊界情況"""
    config = BaseConfig()
    
    # 測試空配置
    with pytest.raises(ConfigError):
        config.validate()
    
    # 測試類型錯誤
    config._data['name'] = 123  # 直接修改內部數據
    with pytest.raises(ConfigError):
        config.validate()

def test_nested_config_operations():
    """測試嵌套配置操作"""
    config = BaseConfig()
    
    # 測試設置嵌套值
    assert config.set("a.b.c", "value") is True
    assert config.get("a.b.c") == "value"
    
    # 測試合併嵌套配置
    config.merge({
        "a": {
            "b": {
                "d": "new_value"
            }
        }
    })
    assert config.get("a.b.c") == "value"
    assert config.get("a.b.d") == "new_value"

def test_process_nested_dict():
    """測試嵌套字典處理"""
    config = BaseConfig()
    
    # 測試基本嵌套
    data = {
        "a.b.c": "value1",
        "a.b.d": "value2",
        "x.y": "value3"
    }
    result = config._process_nested_dict(data)
    assert result == {
        "a": {
            "b": {
                "c": "value1",
                "d": "value2"
            }
        },
        "x": {
            "y": "value3"
        }
    }
    
    # 測試混合嵌套
    data = {
        "a": {
            "b": {
                "c": "value1"
            }
        },
        "x.y": "value2"
    }
    result = config._process_nested_dict(data)
    assert result["a"]["b"]["c"] == "value1"
    assert result["x"]["y"] == "value2"

def test_config_file_operations(tmp_path):
    """測試配置文件操作"""
    config = BaseConfig()
    
    # 測試空配置文件
    empty_file = tmp_path / "empty.json"
    empty_file.write_text("")
    assert config.load_file(empty_file) is True
    
    # 測試無效的配置文件
    invalid_file = tmp_path / "invalid.json"
    invalid_file.write_text("invalid json")
    assert config.load_file(invalid_file) is False
    
    # 測試新配置文件創建
    new_file = tmp_path / "new.json"
    config._config_path = str(new_file)
    config._load_config()
    assert new_file.exists()

def test_env_vars_conversion(monkeypatch):
    """測試環境變量轉換"""
    config = BaseConfig()
    
    # 測試各種類型轉換
    monkeypatch.setenv("TEST_BOOL_VALUE", "true")
    monkeypatch.setenv("TEST_INT_VALUE", "123")
    monkeypatch.setenv("TEST_FLOAT_VALUE", "3.14")
    monkeypatch.setenv("TEST_LIST_VALUE", "[1,2,3]")
    monkeypatch.setenv("TEST_DICT_VALUE", '{"key":"value"}')
    
    config._env_prefix = "TEST_"
    config._load_env_vars()
    
    # 驗證類型轉換
    assert isinstance(config.bool_value, bool)
    assert isinstance(config.int_value, int)
    assert isinstance(config.float_value, float)
    assert isinstance(config.list_value, list)
    assert isinstance(config.dict_value, dict)
    
    # 驗證值
    assert config.bool_value is True
    assert config.int_value == 123
    assert config.float_value == 3.14
    assert config.list_value == [1, 2, 3]
    assert config.dict_value == {"key": "value"}

def test_config_file_error_cases(tmp_path):
    """測試配置文件錯誤情況"""
    config = BaseConfig()
    
    # 測試無法創建目錄
    if os.name != 'nt':  # 非 Windows 系統
        no_perm_dir = tmp_path / "no_perm"
        no_perm_dir.mkdir()
        no_perm_dir.chmod(0o000)
        config._config_path = str(no_perm_dir / "config.json")
        with pytest.raises(ConfigError):
            config._load_config()
    
    # 測試無法讀取文件
    if os.name != 'nt':
        unreadable = tmp_path / "unreadable.json"
        unreadable.write_text("{}")
        unreadable.chmod(0o000)
        config._config_path = str(unreadable)
        with pytest.raises(ConfigError):
            config._load_config()
    
    # 測試無效的 JSON 內容
    invalid_json = tmp_path / "invalid.json"
    invalid_json.write_text("{invalid")
    config._config_path = str(invalid_json)
    with pytest.raises(ConfigError):
        config._load_config()

def test_deep_merge():
    """測試深度合併"""
    config = BaseConfig()
    
    # 測試基本合併
    d1 = {"a": 1, "b": {"c": 2}}
    d2 = {"b": {"d": 3}, "e": 4}
    result = config._deep_merge(d1, d2)
    assert result == {
        "a": 1,
        "b": {
            "c": 2,
            "d": 3
        },
        "e": 4
    }
    
    # 測試覆蓋行為
    d1 = {"a": {"b": 1}}
    d2 = {"a": 2}
    result = config._deep_merge(d1, d2)
    assert result["a"] == 2  # 非字典值應該覆蓋字典 

def test_validation_scenarios():
    """測試各種驗證場景"""
    config = BaseConfig()
    
    # 測試必填字段缺失
    with pytest.raises(ConfigError, match="缺少必填配置項"):
        config.validate()
    
    # 設置必填字段
    config.name = "test"
    
    # 測試類型錯誤
    config._data['bool_value'] = "not a boolean"  # 使用 _data
    config._config['bool_value'] = "not a boolean"  # 使用 _config
    with pytest.raises(ConfigError, match="類型錯誤.*bool"):
        config.validate()
    
    # 測試 Pydantic 驗證錯誤
    config = BaseConfig(name="test")  # 重新創建一個配置
    config._data['bool_value'] = object()  # 使用 _data
    config._config['bool_value'] = object()  # 使用 _config
    with pytest.raises(ConfigError, match="類型錯誤.*bool"):
        config.validate() 

def test_config_file_operations_extended(tmp_path):
    """測試更多配置文件操作場景"""
    config = BaseConfig()
    
    # 測試 YAML 文件
    yaml_file = tmp_path / "config.yaml"
    yaml_file.write_text("""
    app:
      name: test_app
      debug: true
    database:
      url: sqlite:///test.db
    """)
    config.load_file(yaml_file)
    assert config.get("app.name") == "test_app"
    
    # 測試無效的文件格式
    invalid_format = tmp_path / "config.xyz"
    invalid_format.write_text("some data")
    with pytest.raises(ConfigError):
        config.load_file(invalid_format)
    
    # 測試文件權限問題
    if os.name != 'nt':  # 在非 Windows 系統上測試
        no_perm_file = tmp_path / "no_perm.json"
        no_perm_file.write_text("{}")
        no_perm_file.chmod(0o000)
        with pytest.raises(ConfigError):
            config.load_file(no_perm_file) 

def test_env_vars_edge_cases(monkeypatch):
    """測試環境變量邊界情況"""
    config = BaseConfig()
    
    # 測試無效的 JSON
    monkeypatch.setenv("TEST_LIST_VALUE", "[1,2,")  # 無效的 JSON
    monkeypatch.setenv("TEST_DICT_VALUE", "{invalid")
    
    config._env_prefix = "TEST_"
    config._load_env_vars()
    
    # 應該使用預設值
    assert config.list_value == []
    assert config.dict_value == {}
    
    # 測試無效的數字
    monkeypatch.setenv("TEST_INT_VALUE", "not a number")
    monkeypatch.setenv("TEST_FLOAT_VALUE", "invalid")
    config._load_env_vars()
    
    # 應該使用預設值
    assert config.int_value == 0
    assert config.float_value == 0.0 

def test_merge_edge_cases():
    """測試合併邊界情況"""
    config = BaseConfig()
    
    # 測試空字典合併
    config.merge({})
    assert config._config == {}
    
    # 測試嵌套字典覆蓋
    config.merge({"a": {"b": 1}})
    config.merge({"a": 2})  # 非字典值應該覆蓋字典
    assert config.get("a") == 2
    
    # 測試列表合併
    config.merge({"list_value": [1, 2]})
    config.merge({"list_value": [3, 4]})
    assert config.list_value == [3, 4]  # 列表應該被覆蓋而不是合併 

def test_config_file_permissions(tmp_path):
    """測試配置文件權限問題"""
    config = BaseConfig()
    
    # 測試目錄權限問題
    no_perm_dir = tmp_path / "no_perm"
    no_perm_dir.mkdir()
    if os.name != 'nt':  # 在非 Windows 系統上測試
        no_perm_dir.chmod(0o000)
        config_file = no_perm_dir / "config.json"
        with pytest.raises(ConfigError):
            config.load_file(config_file)
    
    # 測試文件權限問題
    if os.name != 'nt':
        test_file = tmp_path / "test.json"
        test_file.write_text("{}")
        test_file.chmod(0o000)
        with pytest.raises(ConfigError):
            config.load_file(test_file) 

def test_update_edge_cases():
    """測試更新邊界情況"""
    config = BaseConfig()
    
    # 測試無效的更新數據
    assert config.update(None) is False
    assert config.update({"invalid": object()}) is False
    
    # 測試更新不存在的字段
    assert config.update({"nonexistent": "value"}) is True
    assert not hasattr(config, "nonexistent")
    
    # 測試更新只讀字段
    original_config = config._config.copy()
    assert config.update({"_config": {}}) is True
    assert config._config == original_config  # 不應該被更新 

def test_validation_complex_types():
    """測試複雜類型驗證"""
    config = BaseConfig()
    config.name = "test"
    
    # 測試字典類型
    config._data['dict_value'] = ["not", "a", "dict"]
    with pytest.raises(ConfigError, match="類型錯誤.*dict"):
        config.validate()
    
    # 測試列表類型
    config._data['dict_value'] = {}  # 修復字典錯誤
    config._data['list_value'] = {"not": "a list"}
    with pytest.raises(ConfigError, match="類型錯誤.*list"):
        config.validate()
    
    # 測試嵌套類型
    config._data['list_value'] = []  # 修復列表錯誤
    config._data['dict_value'] = {
        "nested": {
            "invalid": object()
        }
    }
    with pytest.raises(ConfigError):
        config.validate() 

def test_config_file_load_save():
    """測試配置文件的加載和保存"""
    config = BaseConfig()
    
    # 測試加載不存在的配置
    config._config_path = "nonexistent.json"
    config._load_config()  # 應該創建新文件
    assert Path(config._config_path).exists()
    
    # 測試保存配置
    config.name = "test"
    config.bool_value = True
    assert config.save() is True
    
    # 測試加載已存在的配置
    new_config = BaseConfig()
    new_config._config_path = config._config_path
    new_config._load_config()
    assert new_config.name == "test"
    assert new_config.bool_value is True
    
    # 清理測試文件
    Path(config._config_path).unlink() 

def test_env_vars_load_save(monkeypatch):
    """測試環境變量的加載和保存"""
    config = BaseConfig()
    
    # 測試加載環境變量
    monkeypatch.setenv("TEST_NAME", "env_test")
    monkeypatch.setenv("TEST_BOOL_VALUE", "true")
    config._env_prefix = "TEST_"
    config._load_env_vars()
    
    assert config.name == "env_test"
    assert config.bool_value is True
    
    # 測試保存包含環境變量的配置
    data = config.to_dict(include_env=True)
    assert "name" in data  # 檢查清理後的鍵名
    assert "bool_value" in data
    assert data["name"] == "env_test"
    assert data["bool_value"] == "true"
    
    # 測試不包含環境變量的保存
    data = config.to_dict(include_env=False)
    assert "name" not in data
    assert "bool_value" not in data

def test_validation_with_model():
    """測試與 Pydantic 模型相關的驗證"""
    config = BaseConfig()
    config.name = "test"
    
    # 測試模型驗證
    config._data['bool_value'] = True
    config._data['int_value'] = 123
    config.validate()  # 應該通過
    
    # 測試模型驗證失敗
    config._data['int_value'] = "not an int"
    with pytest.raises(ConfigError, match="類型錯誤"):  # 修改錯誤信息匹配
        config.validate()
    
    # 測試嵌套結構驗證
    config._data['int_value'] = 123  # 修復 int_value
    config._data['dict_value'] = {
        "nested": {
            "value": 123
        }
    }
    config.validate()  # 應該通過

def test_save_error_cases(tmp_path):
    """測試保存錯誤情況"""
    config = BaseConfig()
    
    # 測試未設置配置路徑
    assert config.save() is False
    
    # 測試無法創建目錄
    if os.name != 'nt':
        no_perm_dir = tmp_path / "no_perm"
        no_perm_dir.mkdir()
        no_perm_dir.chmod(0o000)
        config._config_path = str(no_perm_dir / "config.json")
        assert config.save() is False
    
    # 測試無法寫入文件
    if os.name != 'nt':
        unwritable = tmp_path / "unwritable.json"
        unwritable.write_text("{}")
        unwritable.chmod(0o444)  # 只讀
        config._config_path = str(unwritable)
        assert config.save() is False 

def test_merge_error_cases():
    """測試合併錯誤情況"""
    config = BaseConfig()
    
    # 測試無效的數據類型
    with pytest.raises(ConfigError):
        config.merge({"invalid": object()})
    
    # 測試嵌套無效數據
    with pytest.raises(ConfigError):
        config.merge({
            "dict_value": {
                "nested": object()
            }
        })
    
    # 測試 None 值
    with pytest.raises(ConfigError):
        config.merge(None) 

def test_config_file_operations_full(tmp_path):
    """測試完整的配置文件操作"""
    config = BaseConfig()
    
    # 測試創建新配置
    config_path = tmp_path / "config.json"
    config._config_path = str(config_path)
    config._load_config()
    assert config_path.exists()
    assert config_path.read_text() == "{}"
    
    # 測試加載空配置
    empty_file = tmp_path / "empty.json"
    empty_file.write_text("")
    config._config_path = str(empty_file)
    config._load_config()  # 不應拋出錯誤
    
    # 測試加載無效配置
    invalid_file = tmp_path / "invalid.json"
    invalid_file.write_text("invalid json")
    config._config_path = str(invalid_file)
    with pytest.raises(ConfigError):
        config._load_config()
    
    # 測試加載有效配置
    valid_file = tmp_path / "valid.json"
    valid_file.write_text('{"name": "test", "bool_value": true}')
    config._config_path = str(valid_file)
    config._load_config()
    assert config.name == "test"
    assert config.bool_value is True 

def test_convert_value_scenarios():
    """測試值轉換的各種場景"""
    config = BaseConfig()
    
    # 測試布爾值轉換
    field_info = config.model_fields['bool_value']
    assert config._convert_value("true", field_info) is True
    assert config._convert_value("yes", field_info) is True
    assert config._convert_value("1", field_info) is True
    assert config._convert_value("on", field_info) is True
    assert config._convert_value("false", field_info) is False
    assert config._convert_value("no", field_info) is False
    
    # 測試數字轉換
    field_info = config.model_fields['int_value']
    assert config._convert_value("123", field_info) == 123
    assert config._convert_value("invalid", field_info) == 0  # 使用默認值
    
    field_info = config.model_fields['float_value']
    assert config._convert_value("3.14", field_info) == 3.14
    assert config._convert_value("invalid", field_info) == 0.0  # 使用默認值
    
    # 測試列表轉換
    field_info = config.model_fields['list_value']
    assert config._convert_value("[1,2,3]", field_info) == [1, 2, 3]
    assert config._convert_value("a,b,c", field_info) == ["a", "b", "c"]
    assert config._convert_value("invalid", field_info) == []  # 使用默認值
    
    # 測試字典轉換
    field_info = config.model_fields['dict_value']
    assert config._convert_value('{"key":"value"}', field_info) == {"key": "value"}
    assert config._convert_value("invalid", field_info) == {}  # 使用默認值
    
    # 測試其他類型
    field_info = config.model_fields['name']  # 使用字符串類型的字段
    assert config._convert_value("test", field_info) == "test"  # 保持原樣 

def test_nested_dict_processing():
    """測試嵌套字典處理的更多場景"""
    config = BaseConfig()
    
    # 測試多層嵌套
    data = {
        "a.b.c.d": 1,
        "a.b.c.e": 2,
        "x.y.z": 3
    }
    result = config._process_nested_dict(data)
    assert result == {
        "a": {
            "b": {
                "c": {
                    "d": 1,
                    "e": 2
                }
            }
        },
        "x": {
            "y": {
                "z": 3
            }
        }
    }
    
    # 測試混合點號和字典
    data = {
        "a": {
            "b.c": 1,
            "d": {
                "e.f": 2
            }
        },
        "x.y": {
            "z": 3
        }
    }
    result = config._process_nested_dict(data)
    assert result["a"]["b"]["c"] == 1
    assert result["a"]["d"]["e"]["f"] == 2
    assert result["x"]["y"]["z"] == 3 

def test_deep_merge_scenarios():
    """測試深度合併的各種場景"""
    config = BaseConfig()
    
    # 測試列表合併
    d1 = {"list": [1, 2]}
    d2 = {"list": [3, 4]}
    result = config._deep_merge(d1, d2)
    assert result["list"] == [3, 4]  # 列表應該被覆蓋
    
    # 測試字典合併
    d1 = {"dict": {"a": 1, "b": 2}}
    d2 = {"dict": {"b": 3, "c": 4}}
    result = config._deep_merge(d1, d2)
    assert result["dict"] == {"a": 1, "b": 3, "c": 4}
    
    # 測試混合類型
    d1 = {"key": {"nested": [1, 2]}}
    d2 = {"key": {"nested": {"a": 3}}}
    result = config._deep_merge(d1, d2)
    assert result["key"]["nested"] == {"a": 3}  # 不同類型應該被覆蓋 