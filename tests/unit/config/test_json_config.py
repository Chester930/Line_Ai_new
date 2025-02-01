import pytest
import json
import tempfile
from pathlib import Path
from typing import Dict, Optional
import os
import shutil
from pydantic import Field

from src.shared.config.json_config import (
    JSONConfig, 
    JSONConfigLoader,
    PathEncoder,
    Settings
)
from src.shared.config.validator import ConfigValidator, ValidationRule
from src.shared.utils.exceptions import ConfigError

def get_test_config():
    """獲取測試配置類"""
    class TestConfig(JSONConfig):
        """測試用配置類"""
        app_name: str = Field(default="test_app")
        debug: bool = Field(default=False)
        port: int = Field(default=8000)
        api_key: Optional[str] = Field(default=None)
        settings: Dict[str, str] = Field(default_factory=dict)
        data_path: Optional[Path] = Field(default=None, description="數據路徑")

    return TestConfig

@pytest.fixture
def config_file():
    """創建臨時配置文件"""
    with tempfile.NamedTemporaryFile(mode='w+', suffix='.json', delete=False) as f:
        json.dump({
            "api_key": "test_key",
            "port": 8000,
            "debug": False
        }, f)
        f.flush()
        yield Path(f.name)
        
    # 清理文件
    try:
        Path(f.name).unlink()
    except FileNotFoundError:
        pass

@pytest.fixture
def temp_config_dir():
    """創建臨時配置目錄"""
    temp_dir = Path(tempfile.mkdtemp())
    yield temp_dir
    shutil.rmtree(temp_dir)

def test_load_config(config_file):
    """測試加載配置"""
    test_config = get_test_config()
    config = test_config(config_path=config_file, api_key=None)
    
    # 驗證默認值
    assert config.app_name == "test_app"
    assert config.debug is False
    assert config.port == 8000
    assert config.api_key is None
    assert config.settings == {}

def test_load_invalid_json(tmp_path):
    """測試加載無效的 JSON"""
    invalid_file = tmp_path / "invalid.json"
    invalid_file.write_text("{invalid json")
    
    test_config = get_test_config()
    with pytest.raises(json.JSONDecodeError):
        test_config(config_path=invalid_file)

def test_load_nonexistent_file(tmp_path):
    """測試加載不存在的文件"""
    nonexistent_file = tmp_path / "nonexistent.json"
    
    test_config = get_test_config()
    config = test_config(config_path=nonexistent_file)
    
    # 驗證文件被創建
    assert nonexistent_file.exists()
    # 驗證文件內容為空配置
    assert nonexistent_file.read_text() == "{}"
    # 驗證配置對象使用默認值
    assert config.app_name == "test_app"
    assert config.debug is False
    assert config.port == 8000

def test_save_config(tmp_path):
    """測試保存配置"""
    config_file = tmp_path / "config.json"
    test_config = get_test_config()
    
    # 創建並修改配置
    config = test_config(config_path=config_file)
    config.app_name = "updated_app"
    config.port = 9000
    
    # 保存配置
    assert config.save()
    
    # 讀取保存的文件
    saved_data = json.loads(config_file.read_text())
    assert saved_data["app_name"] == "updated_app"
    assert saved_data["port"] == 9000

def test_partial_update(config_file):
    """測試部分更新配置"""
    test_config = get_test_config()
    config = test_config(config_path=config_file)
    
    # 更新部分配置
    config.update({
        "debug": True,
        "port": 9000
    })
    
    assert config.debug is True
    assert config.port == 9000
    # 確保其他值未變
    assert config.app_name == "test_app"

def test_config_validation(tmp_path):
    """測試配置驗證"""
    config_file = tmp_path / "config.json"
    test_config = get_test_config()
    config = test_config(config_path=config_file)
    
    # 創建驗證器
    validator = ConfigValidator()
    validator.add_rule(
        ValidationRule("port")
        .required()
        .min_value(1024)
        .max_value(65535)
    )
    
    # 測試有效值
    config.port = 8080
    assert validator.validate(config)
    
    # 測試無效值
    config.port = 80
    with pytest.raises(ValueError):
        validator.validate(config)

def test_config_with_path_conversion(tmp_path):
    """測試路徑轉換"""
    config_file = tmp_path / "config.json"
    test_config = get_test_config()
    
    # 使用字符串路徑創建配置
    config = test_config(config_path=str(config_file))
    assert isinstance(config.config_path, Path)
    
    # 使用 Path 對象創建配置
    config = test_config(config_path=config_file)
    assert isinstance(config.config_path, Path)

def test_config_directory_creation(tmp_path):
    """測試配置目錄創建"""
    config_dir = tmp_path / "config" / "nested"
    config_file = config_dir / "config.json"
    
    test_config = get_test_config()
    config = test_config(config_path=config_file)
    
    # 保存配置應該創建目錄
    assert config.save()
    assert config_file.parent.exists()
    assert config_file.exists()

def test_config_reload(config_file):
    """測試重新加載配置"""
    test_config = get_test_config()
    config = test_config(config_path=config_file)
    
    # 修改配置文件
    data = json.loads(config_file.read_text())
    data["app_name"] = "modified_app"
    config_file.write_text(json.dumps(data))
    
    # 重新加載
    config.reload()
    assert config.app_name == "modified_app"

def test_path_encoder():
    """測試路徑編碼器"""
    encoder = PathEncoder()
    test_path = Path("/test/path")
    encoded = encoder.default(test_path)
    assert encoded == {"__path__": str(test_path).replace('\\', '/')}

def test_path_encoder_with_nested_paths():
    """測試嵌套路徑的編碼"""
    test_data = {
        "paths": [Path("/path1"), Path("/path2")]
    }
    encoded = json.dumps(test_data, cls=PathEncoder)
    decoded = json.loads(encoded)
    
    assert decoded["paths"] == [
        {"__path__": "/path1"},
        {"__path__": "/path2"}
    ]

def test_config_save_without_path():
    """測試沒有配置路徑時的保存操作"""
    test_config = get_test_config()
    config = test_config()  # 不提供配置路徑
    
    # 保存應該失敗
    assert not config.save()

def test_config_update_with_invalid_data():
    """測試使用無效數據更新配置"""
    test_config = get_test_config()
    config = test_config()
    
    # 使用無效的端口值更新
    with pytest.raises(ValueError):
        config.update({"port": "invalid"})

def test_config_reload_without_path():
    """測試沒有配置路徑時的重新加載操作"""
    test_config = get_test_config()
    config = test_config()
    
    # 重新加載應該失敗
    assert not config.reload()

def test_config_reload_nonexistent_file(temp_config_dir):
    """測試重新載入不存在的配置文件"""
    config_path = temp_config_dir / "nonexistent.json"
    config = TestJSONConfig(config_path=config_path, api_key=None, port=8000, debug=False)
    
    # 確保文件不存在
    if config_path.exists():
        config_path.unlink()
    
    # 測試重新載入
    assert config.reload() is False

def test_config_save_with_permission_error(tmp_path):
    """測試保存時的權限錯誤"""
    config_file = tmp_path / "config.json"
    test_config = get_test_config()
    config = test_config(config_path=config_file)
    
    # 創建只讀文件
    config_file.touch()
    os.chmod(config_file, 0o444)  # 設置為只讀
    
    try:
        # 保存應該失敗
        assert not config.save()
    finally:
        # 恢復權限以便清理
        os.chmod(config_file, 0o666)

class TestJSONConfig(JSONConfig):
    """測試用 JSON 配置類"""
    api_key: Optional[str] = Field(default=None)
    port: int = Field(default=8000)
    debug: bool = Field(default=False)
    data_path: Optional[Path] = Field(default=None, description="數據路徑")

def test_load_nonexistent_config(temp_config_dir):
    """測試載入不存在的配置文件"""
    config_path = temp_config_dir / "nonexistent.json"
    config = TestJSONConfig(config_path=config_path, api_key=None)
    
    # 驗證默認值
    assert config.api_key == None
    assert config.port == 8000
    assert config.debug is False
    assert config_path.exists()

def test_save_config(temp_config_dir):
    """測試保存配置"""
    config_path = temp_config_dir / "new_config.json"
    config = TestJSONConfig(config_path)
    config.api_key = "new_key"
    config.port = 9000
    config.debug = True
    
    assert config.save() is True
    assert config_path.exists()
    
    # 驗證保存的內容
    saved_data = json.loads(config_path.read_text())
    assert saved_data["api_key"] == "new_key"
    assert saved_data["port"] == 9000
    assert saved_data["debug"] is True

def test_update_config(config_file):
    """測試更新配置"""
    config = TestJSONConfig(config_file)
    
    # 更新部分配置
    update_data = {
        "port": 9000,
        "debug": False
    }
    assert config.update(update_data) is True
    assert config.port == 9000
    assert config.debug is False
    assert config.api_key == "test_key"  # 未更新的值保持不變

def test_update_with_invalid_data(config_file):
    """測試使用無效數據更新配置"""
    config = TestJSONConfig(config_file)
    
    # 使用無效的端口值
    with pytest.raises(ValueError):
        config.update({"port": "invalid"})
    
    # 確保配置未被更改
    assert config.port == 8000

def test_reload_config(config_file):
    """測試重新載入配置"""
    config = TestJSONConfig(config_file)
    original_port = config.port
    
    # 修改配置文件
    new_data = {
        "api_key": "test_key",
        "port": 9000,
        "debug": False
    }
    config_file.write_text(json.dumps(new_data))
    
    # 重新載入
    assert config.reload() is True
    assert config.port == 9000
    assert config.port != original_port

def test_get_config_value(config_file):
    """測試獲取配置值"""
    config = TestJSONConfig(config_file)
    assert config.get("api_key") == "test_key"
    assert config.get("port") == 8000
    assert config.get("nonexistent", "default") == "default"

def test_set_config_value(config_file):
    """測試設置配置值"""
    config = TestJSONConfig(config_file)
    assert config.set("new_key", "value") is True
    assert config.get("new_key") == "value"
    
    # 測試設置嵌套值
    assert config.set("nested.key", "nested_value") is True
    assert config.get("nested.key") == "nested_value"
    
    # 測試設置空鍵
    assert config.set("", "value") is False
    assert config.set(None, "value") is False

def test_path_handling(temp_config_dir):
    """測試路徑處理"""
    config_path = temp_config_dir / "path_config.json"
    config = TestJSONConfig(config_path)
    
    test_path = Path("/test/path")
    config.set("test_path", test_path)
    assert config.save() is True
    
    # 重新載入並驗證
    new_config = TestJSONConfig(config_path)
    loaded_path = new_config.get("test_path")
    assert isinstance(loaded_path, Path)
    assert str(loaded_path) == str(test_path)

def test_init_with_data():
    """測試使用數據初始化配置"""
    config = TestJSONConfig(api_key="test_key", port=9000)
    assert config.api_key == "test_key"
    assert config.port == 9000
    assert config.debug is False

def test_init_with_config_path(config_file):
    """測試使用配置文件路徑初始化"""
    # 創建配置文件
    config_data = {
        "api_key": "file_key",
        "port": 9000,
        "debug": True
    }
    config_file.write_text(json.dumps(config_data))
    
    # 初始化配置
    config = TestJSONConfig(config_path=config_file)
    assert config.api_key == "file_key"
    assert config.port == 9000
    assert config.debug is True

def test_path_handling(config_file):
    """測試路徑處理"""
    test_path = Path("/test/path")
    config = TestJSONConfig(
        config_path=config_file,
        data_path=test_path
    )
    
    # 保存配置
    config.save()
    
    # 讀取配置
    saved_data = json.loads(config_file.read_text())
    assert saved_data["data_path"] == str(test_path)
    
    # 重新載入配置
    new_config = TestJSONConfig(config_path=config_file)
    assert isinstance(new_config.data_path, Path)
    assert new_config.data_path == test_path

def test_config_get_set_operations(tmp_path):
    """測試配置的 get/set 操作"""
    config_file = tmp_path / "config.json"
    test_config = get_test_config()
    config = test_config(config_path=config_file)
    
    # 測試 get 操作
    assert config.get("app_name") == "test_app"
    assert config.get("nonexistent", "default") == "default"
    
    # 測試嵌套 get 操作
    config.set("nested.key", "value")
    assert config.get("nested.key") == "value"
    
    # 測試 set 操作
    assert config.set("debug", True)
    assert config.debug is True
    
    # 測試無效的 set 操作
    assert not config.set("", "value")  # 空鍵
    assert not config.set(None, "value")  # None 鍵
    assert not config.set("invalid.key", "value")  # 無效的嵌套路徑

def test_config_type_conversion(tmp_path):
    """測試配置值的類型轉換"""
    config_file = tmp_path / "config.json"
    test_config = get_test_config()
    config = test_config(config_path=config_file)
    
    # 測試布爾值轉換
    os.environ["TEST_DEBUG"] = "true"
    config = test_config(config_path=config_file)
    assert config.debug is True
    
    # 測試整數轉換
    os.environ["TEST_PORT"] = "9000"
    config = test_config(config_path=config_file)
    assert config.port == 9000
    
    # 測試路徑轉換
    test_path = "/test/path"
    os.environ["TEST_DATA_PATH"] = test_path
    config = test_config(config_path=config_file)
    assert isinstance(config.data_path, Path)
    assert str(config.data_path) == test_path
    
    # 清理環境變量
    del os.environ["TEST_DEBUG"]
    del os.environ["TEST_PORT"]
    del os.environ["TEST_DATA_PATH"]

def test_config_nested_settings(tmp_path):
    """測試嵌套設置的處理"""
    config_file = tmp_path / "config.json"
    test_config = get_test_config()
    
    # 設置嵌套環境變量
    os.environ["TEST_SETTINGS__DATABASE__HOST"] = "localhost"
    os.environ["TEST_SETTINGS__DATABASE__PORT"] = "5432"
    os.environ["TEST_SETTINGS__API__VERSION"] = "v1"
    
    config = test_config(config_path=config_file)
    
    # 驗證嵌套設置
    assert config.settings["database"]["host"] == "localhost"
    assert config.settings["database"]["port"] == "5432"
    assert config.settings["api"]["version"] == "v1"
    
    # 清理環境變量
    del os.environ["TEST_SETTINGS__DATABASE__HOST"]
    del os.environ["TEST_SETTINGS__DATABASE__PORT"]
    del os.environ["TEST_SETTINGS__API__VERSION"]

def test_config_validation_with_custom_rules(tmp_path):
    """測試自定義驗證規則"""
    config_file = tmp_path / "config.json"
    test_config = get_test_config()
    config = test_config(config_path=config_file)
    
    # 創建自定義驗證規則
    def validate_port(value):
        return isinstance(value, int) and value % 2 == 0
    
    validator = ConfigValidator()
    validator.add_rule(
        ValidationRule("port")
        .required()
        .custom(validate_port, "Port must be an even number")
    )
    
    # 測試有效值
    config.port = 8080
    assert validator.validate(config)
    
    # 測試無效值
    config.port = 8081
    with pytest.raises(ValueError) as exc:
        validator.validate(config)
    assert "Port must be an even number" in str(exc.value)

def test_config_merge_behavior(tmp_path):
    """測試配置合併行為"""
    config_file = tmp_path / "config.json"
    
    # 創建初始配置
    initial_data = {
        "app_name": "initial_app",
        "settings": {
            "database": {
                "host": "localhost"
            }
        }
    }
    
    with open(config_file, 'w') as f:
        json.dump(initial_data, f)
    
    test_config = get_test_config()
    config = test_config(
        config_path=config_file,
        app_name="override_app",
        settings={"api": {"key": "test"}}
    )
    
    # 驗證合併結果
    assert config.app_name == "override_app"  # 參數覆蓋文件
    assert config.settings["database"]["host"] == "localhost"  # 保留文件中的設置
    assert config.settings["api"]["key"] == "test"  # 添加新的設置

def test_config_environment_override(tmp_path):
    """測試環境變量覆蓋"""
    config_file = tmp_path / "config.json"
    
    # 創建初始配置
    initial_data = {
        "app_name": "file_app",
        "port": 8000,
        "debug": False
    }
    
    with open(config_file, 'w') as f:
        json.dump(initial_data, f)
    
    # 設置環境變量
    os.environ["TEST_APP_NAME"] = "env_app"
    os.environ["TEST_PORT"] = "9000"
    os.environ["TEST_DEBUG"] = "true"
    
    test_config = get_test_config()
    config = test_config(
        config_path=config_file,
        app_name="param_app"  # 參數優先級最高
    )
    
    # 驗證優先級：參數 > 環境變量 > 文件 > 默認值
    assert config.app_name == "param_app"
    assert config.port == 9000  # 來自環境變量
    assert config.debug is True  # 來自環境變量
    
    # 清理環境變量
    del os.environ["TEST_APP_NAME"]
    del os.environ["TEST_PORT"]
    del os.environ["TEST_DEBUG"]

@pytest.fixture
def temp_config_file():
    """創建臨時配置文件"""
    with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
        json.dump({
            "app_name": "test_app",
            "debug": True,
            "database": {
                "url": "sqlite:///test.db",
                "echo": False
            }
        }, f)
        return Path(f.name)

def test_json_config_load(temp_config_file):
    """測試 JSON 配置加載"""
    config = JSONConfig()
    config._config_path = str(temp_config_file)
    config._load_config()
    
    # 使用字符串比較而不是 Path 對象
    assert str(config.get("database.url")) == "sqlite:///test.db"

def test_json_config_save(temp_config_file):
    """測試 JSON 配置保存"""
    config = JSONConfig(config_path=str(temp_config_file))
    config.set("new_key", "new_value")
    assert config.save()
    
    # 驗證保存的內容
    loaded_data = json.loads(temp_config_file.read_text())
    assert loaded_data["new_key"] == "new_value"

def test_json_config_nested_update(temp_config_file):
    """測試嵌套配置更新"""
    config = JSONConfig(config_path=str(temp_config_file))
    config.set("database.port", 5432)
    assert config.get("database.port") == 5432
    
    config.update({
        "database": {
            "username": "test",
            "password": "secret"
        }
    })
    assert config.get("database.username") == "test"
    assert config.get("database.password") == "secret"

@pytest.fixture
def json_config():
    """返回 JSONConfig 實例"""
    return JSONConfig()

@pytest.fixture
def sample_config_file(tmp_path):
    config_file = tmp_path / "config.json"
    config_file.write_text("""
    {
        "app": {
            "name": "test_app",
            "version": "1.0.0",
            "debug": true
        },
        "database": {
            "url": "sqlite:///test.db",
            "echo": false
        },
        "api": {
            "key": "test_key",
            "timeout": 30
        }
    }
    """)
    return config_file

def test_load_config(json_config, sample_config_file):
    """測試加載配置文件"""
    # 測試加載有效配置
    json_config.load(sample_config_file)
    assert json_config.get("app.name") == "test_app"
    assert json_config.get("database.url") == "sqlite:///test.db"
    assert json_config.get("api.key") == "test_key"
    
    # 測試加載不存在的文件
    with pytest.raises(JsonConfigError):
        json_config.load("nonexistent.json")
    
    # 測試加載無效的 JSON
    invalid_file = sample_config_file.parent / "invalid.json"
    invalid_file.write_text("invalid json")
    with pytest.raises(JsonConfigError):
        json_config.load(invalid_file)

def test_save_config(json_config, tmp_path):
    """測試保存配置"""
    # 設置一些配置值
    json_config.set("app.name", "new_app")
    json_config.set("database.url", "mysql://localhost/db")
    
    # 保存配置
    config_file = tmp_path / "saved_config.json"
    json_config.save(config_file)
    
    # 重新加載並驗證
    new_config = JSONConfig()
    new_config.load(config_file)
    assert new_config.get("app.name") == "new_app"
    assert new_config.get("database.url") == "mysql://localhost/db"

def test_get_set_nested(json_config):
    """測試嵌套配置的獲取和設置"""
    # 設置嵌套值
    json_config.set("a.b.c", "value")
    assert json_config.get("a.b.c") == "value"
    
    # 設置多層嵌套
    json_config.set("x.y.z.w", 123)
    assert json_config.get("x.y.z.w") == 123

def test_merge_config(json_config):
    """測試配置合併"""
    # 初始配置
    json_config.set("app.name", "app1")
    json_config.set("app.version", "1.0")
    
    # 合併新配置
    json_config.merge({
        "app": {
            "version": "2.0",
            "debug": True
        },
        "new_key": "value"
    })
    
    assert json_config.get("app.name") == "app1"  # 保持不變
    assert json_config.get("app.version") == "2.0"  # 被覆蓋
    assert json_config.get("app.debug") is True  # 新增
    assert json_config.get("new_key") == "value"  # 新增

def test_json_config_basic():
    """測試基本的 JSON 配置功能"""
    config = JSONConfig()
    
    # 測試設置和獲取值
    config.set("app.name", "test_app")
    assert config.get("app.name") == "test_app"
    
    # 測試嵌套配置，使用字符串比較
    config.set("database.settings.url", "sqlite:///test.db")
    assert str(config.get("database.settings.url")) == "sqlite:///test.db"
    
    # 測試默認值
    assert config.get("nonexistent", "default") == "default"

def test_json_config_file_operations(tmp_path):
    """測試配置文件操作"""
    config_file = tmp_path / "config.json"
    config = JSONConfig(config_path=config_file)
    
    # 測試保存配置
    config.set("test_key", "test_value")
    assert config.save()
    assert config_file.exists()
    
    # 測試加載配置
    new_config = JSONConfig(config_path=config_file)
    assert new_config.get("test_key") == "test_value"
    
    # 測試重新加載
    config_file.write_text('{"test_key": "new_value"}')
    assert new_config.reload()
    assert new_config.get("test_key") == "new_value"

def test_json_config_error_handling(tmp_path):
    """測試錯誤處理"""
    config = JSONConfig()
    
    # 測試加載不存在的文件
    with pytest.raises(ValueError, match="配置文件不存在"):
        config.load(tmp_path / "nonexistent.json")
    
    # 測試加載無效的 JSON
    invalid_file = tmp_path / "invalid.json"
    invalid_file.write_text("{invalid json")
    with pytest.raises(ValueError, match="無效的 JSON 格式"):
        config.load(invalid_file)
    
    # 測試無效的配置值
    with pytest.raises(ValueError):
        config.set("port", "not_a_number")
    
    # 測試無效的合併數據
    assert not config.merge(None)
    assert not config.merge({"invalid.key": "value"})

def test_json_config_loader(tmp_path):
    """測試配置加載器"""
    config_file = tmp_path / "config.json"
    
    # 創建測試配置文件
    test_data = {
        "app_name": "test_app",
        "port": 8080,
        "debug": True,
        "settings": {
            "database": {"host": "localhost"},
            "api": {"version": "v1"}
        }
    }
    config_file.write_text(json.dumps(test_data))
    
    # 測試加載
    loader = JSONConfigLoader(config_file)
    config = loader.load(JSONConfig)
    
    assert config.get("app_name") == "test_app"
    assert config.get("port") == 8080
    assert config.get("debug") is True
    assert config.get("settings.database.host") == "localhost"
    
    # 測試保存
    config.set("new_key", "new_value")
    assert loader.save(config)
    
    # 驗證保存的內容
    saved_data = json.loads(config_file.read_text())
    assert saved_data["new_key"] == "new_value"

def test_env_override_comprehensive(monkeypatch):
    """全面測試環境變量覆蓋"""
    config = JSONConfig()
    
    # 1. 基本類型覆蓋
    monkeypatch.setenv("TEST_DEBUG", "true")
    monkeypatch.setenv("TEST_PORT", "9000")
    config._apply_env_override()
    assert config.debug is True
    assert config.port == 9000
    
    # 2. 嵌套設置覆蓋
    monkeypatch.setenv("TEST_SETTINGS__DATABASE__HOST", "127.0.0.1")
    monkeypatch.setenv("TEST_SETTINGS__DATABASE__PORT", "5432")
    monkeypatch.setenv("TEST_SETTINGS__API__VERSION", "v2")
    config._apply_env_override()
    
    assert config.settings.database["host"] == "127.0.0.1"
    assert config.settings.database["port"] == "5432"
    assert config.settings.api["version"] == "v2"
    
    # 3. 特殊類型轉換
    test_path = "/test/path"
    monkeypatch.setenv("TEST_DATA_PATH", test_path)
    config._apply_env_override()
    assert isinstance(config.data_path, Path)
    assert str(config.data_path) == test_path
    
    # 4. 錯誤處理
    monkeypatch.setenv("TEST_PORT", "invalid")  # 無效的整數
    config._apply_env_override()
    assert config.port == 9000  # 保持原值
    
    monkeypatch.setenv("TEST_DEBUG", "invalid")  # 無效的布爾值
    config._apply_env_override()
    assert config.debug is True  # 保持原值

def test_path_encoder_edge_cases():
    """測試 PathEncoder 的邊界情況"""
    encoder = PathEncoder()
    
    # 1. 特殊路徑
    special_paths = [
        (".", "."),                  # 當前目錄
        ("..", ".."),               # 父目錄
        ("~/test", "~/test"),       # 家目錄
        ("/", "/"),                 # 根目錄
        ("C:/", "C:/"),            # Windows 根目錄
    ]
    
    for input_path, expected in special_paths:
        result = encoder.default(Path(input_path))
        assert result == {"__path__": expected}
    
    # 2. URL 處理
    urls = [
        "http://example.com",
        "https://test.com/path",
        "ftp://server/file",
        "file:///path/to/file"
    ]
    
    for url in urls:
        assert encoder.default(url) == url
    
    # 3. 混合路徑
    mixed_data = {
        "web_url": "http://example.com",
        "file_path": Path("/path/to/file"),
        "nested": {
            "url": "https://test.com",
            "path": Path("relative/path")
        }
    }
    
    encoded = json.dumps(mixed_data, cls=PathEncoder)
    decoded = json.loads(encoded)
    
    assert decoded["web_url"] == "http://example.com"
    assert decoded["file_path"] == {"__path__": "/path/to/file"}
    assert decoded["nested"]["url"] == "https://test.com"
    assert decoded["nested"]["path"] == {"__path__": "relative/path"}
    
    # 4. 特殊情況處理
    assert encoder.default(Path()) == {"__path__": "."}  # 空路徑
    
    # 5. 錯誤處理
    class UnserializableObject:
        pass
    
    with pytest.raises(TypeError):
        encoder.default(UnserializableObject())

def test_settings_comprehensive():
    """全面測試 Settings 類"""
    # 1. 基本初始化
    settings = Settings()
    assert settings.database == {"host": "localhost", "port": "5432"}
    assert settings.api == {"version": "v1"}
    
    # 2. 自定義初始化
    custom_settings = Settings(
        database={"host": "127.0.0.1", "port": "3306"},
        api={"version": "v2"}
    )
    assert custom_settings.database["host"] == "127.0.0.1"
    assert custom_settings.database["port"] == "3306"
    assert custom_settings.api["version"] == "v2"
    
    # 3. 動態屬性
    settings.new_section = {"key": "value"}
    assert settings.new_section["key"] == "value"
    
    # 4. 嵌套更新
    settings.database.update({
        "username": "admin",
        "password": "secret"
    })
    assert settings.database["username"] == "admin"
    assert settings.database["password"] == "secret"
    
    # 5. 序列化
    data = settings.model_dump()
    assert isinstance(data, dict)
    assert data["database"]["host"] == "localhost"
    assert data["new_section"]["key"] == "value"
    
    # 6. 驗證
    with pytest.raises(ValueError):
        Settings(database="not_a_dict")  # 類型錯誤
    
    with pytest.raises(ValueError):
        Settings(api=123)  # 類型錯誤

def test_config_file_operations_full():
    """全面測試配置文件操作"""
    with tempfile.TemporaryDirectory() as temp_dir:
        config_file = Path(temp_dir) / "config.json"
        
        # 1. 創建新配置
        config = JSONConfig(config_path=config_file)
        assert config_file.exists()
        
        # 2. 保存配置
        config.debug = True
        config.port = 9000
        assert config.save()
        
        # 3. 加載配置
        loaded = JSONConfig(config_path=config_file)
        assert loaded.debug is True
        assert loaded.port == 9000
        
        # 4. 更新配置
        config.set("new_key", "value")
        assert config.save()
        
        # 5. 重新加載
        assert loaded.reload()
        assert loaded.get("new_key") == "value"
        
        # 6. 錯誤處理
        invalid_file = Path(temp_dir) / "invalid.json"
        invalid_file.write_text("invalid json")
        with pytest.raises(ValueError):
            JSONConfig(config_path=invalid_file)

def test_config_validation_full():
    """全面測試配置驗證"""
    config = JSONConfig()
    
    # 1. 基本驗證
    assert config._validate_data({})  # 空配置
    assert config._validate_data({"debug": True})  # 單一值
    assert config._validate_data({"port": 8080})  # 單一值
    
    # 2. 嵌套驗證
    nested = {
        "settings": {
            "database": {"host": "localhost"},
            "api": {"version": "v1"}
        }
    }
    assert config._validate_data(nested)
    
    # 3. 錯誤驗證
    invalid = [
        ({"debug": "not_bool"}, "debug 必須是布爾值"),
        ({"port": "not_int"}, "port 必須是整數"),
        ({"settings": "not_dict"}, "settings 必須是字典"),
        ({"settings": {"database": "not_dict"}}, "settings.database 必須是字典")
    ]
    
    for data, error in invalid:
        assert not config._validate_data(data)

def test_config_update_full():
    """全面測試配置更新"""
    config = JSONConfig()
    
    # 1. 基本更新
    assert config.update({
        "debug": True,
        "port": 9000
    })
    assert config.debug is True
    assert config.port == 9000
    
    # 2. 嵌套更新
    assert config.update({
        "settings": {
            "database": {
                "host": "localhost",
                "port": "5432"
            }
        }
    })
    assert config.settings.database["host"] == "localhost"
    assert config.settings.database["port"] == "5432"
    
    # 3. 錯誤處理
    # 3.1 無效的輸入
    assert not config.update(None)  # None
    assert not config.update({})    # 空字典
    
    # 3.2 無效的鍵
    assert not config.update({"": "value"})  # 空鍵
    assert not config.update({123: "value"})  # 非字符串鍵
    assert not config.update({"a.b": "value"})  # 包含點的鍵
    
    # 3.3 無效的值
    assert not config.update({"port": "not_a_number"})  # 類型錯誤
    assert not config.update({"debug": "not_a_bool"})  # 類型錯誤
    assert not config.update({"settings": "not_a_dict"})  # 類型錯誤 

def test_config_merge_comprehensive():
    """全面測試配置合併"""
    config = JSONConfig()
    
    # 1. 基本合併
    assert config.merge({
        "debug": True,
        "port": 9000
    })
    assert config.debug is True
    assert config.port == 9000
    
    # 2. 深度合併
    assert config.merge({
        "settings": {
            "database": {
                "host": "localhost",
                "port": "5432",
                "credentials": {
                    "username": "admin"
                }
            },
            "api": {
                "version": "v2"
            }
        }
    })
    
    # 3. 驗證結果
    assert config.settings.database["host"] == "localhost"
    assert config.settings.database["port"] == "5432"
    assert config.settings.database["credentials"]["username"] == "admin"
    assert config.settings.api["version"] == "v2"
    
    # 4. 錯誤處理
    assert not config.merge(None)  # None
    assert not config.merge({})    # 空字典
    assert not config.merge({"invalid.key": "value"})  # 無效鍵
    assert not config.merge({"settings": "not_a_dict"})  # 無效值 

def test_path_handling_comprehensive():
    """全面測試路徑處理"""
    with tempfile.TemporaryDirectory() as temp_dir:
        config_file = Path(temp_dir) / "config.json"
        config = JSONConfig(config_path=config_file)
        
        # 1. 基本路徑處理
        test_paths = {
            "unix_path": Path("/usr/local/bin"),
            "win_path": Path("C:/Program Files"),
            "relative_path": Path("./config"),
            "parent_path": Path("../data")
        }
        
        for key, path in test_paths.items():
            config.set(key, path)
        
        # 2. 保存和加載
        assert config.save()
        loaded = JSONConfig(config_path=config_file)
        
        # 3. 驗證路徑
        for key, path in test_paths.items():
            assert isinstance(loaded.get(key), Path)
            assert str(loaded.get(key)) == str(path)
        
        # 4. URL 處理
        urls = {
            "http_url": "http://example.com",
            "https_url": "https://test.com/path",
            "ftp_url": "ftp://server/file"
        }
        
        for key, url in urls.items():
            config.set(key, url)
            assert config.get(key) == url 

def test_config_loader_comprehensive():
    """全面測試配置加載器"""
    with tempfile.TemporaryDirectory() as temp_dir:
        config_file = Path(temp_dir) / "config.json"
        
        # 1. 基本加載
        test_data = {
            "debug": True,
            "port": 8080,
            "settings": {
                "database": {"host": "localhost"}
            }
        }
        config_file.write_text(json.dumps(test_data))
        
        loader = JSONConfigLoader(config_file)
        config = loader.load(JSONConfig)
        
        assert config.get("app_name") == "test_app"
        assert config.get("port") == 8080
        assert config.get("debug") is True
        assert config.get("settings.database.host") == "localhost"
        
        # 2. 保存和重新加載
        config.set("new_key", "value")
        assert loader.save(config)
        
        reloaded = loader.load(JSONConfig)
        assert reloaded.get("new_key") == "value"
        
        # 3. 錯誤處理
        nonexistent = Path(temp_dir) / "nonexistent.json"
        with pytest.raises(FileNotFoundError):
            JSONConfigLoader(nonexistent).load(JSONConfig)
        
        invalid_file = Path(temp_dir) / "invalid.json"
        invalid_file.write_text("invalid json")
        with pytest.raises(ValueError):
            JSONConfigLoader(invalid_file).load(JSONConfig) 

def test_config_initialization_comprehensive():
    """全面測試配置初始化"""
    # 1. 基本初始化
    config = JSONConfig()
    assert isinstance(config, JSONConfig)
    assert config._config == {}
    assert config._initial_values == {}
    
    # 2. 帶參數初始化
    config = JSONConfig(
        debug=True,
        port=9000,
        settings={"database": {"host": "localhost"}}
    )
    assert config.debug is True
    assert config.port == 9000
    assert config.settings.database["host"] == "localhost"
    
    # 3. 帶配置文件初始化
    with tempfile.TemporaryDirectory() as temp_dir:
        config_file = Path(temp_dir) / "config.json"
        config_file.write_text('{"debug": true, "port": 8080}')
        config = JSONConfig(config_path=config_file)
        assert config.debug is True
        assert config.port == 8080
        
        # 4. 錯誤處理
        with pytest.raises(ValueError):
            JSONConfig(port="invalid")  # 無效的端口值
        with pytest.raises(ValueError):
            JSONConfig(debug="not_bool")  # 無效的布爾值
        with pytest.raises(ValueError):
            JSONConfig(settings="not_dict")  # 無效的設置值 

def test_config_sync_comprehensive():
    """全面測試配置同步"""
    config = JSONConfig()
    
    # 1. 基本同步
    config.debug = True
    config.port = 9000
    config._sync_config()
    assert config._config["debug"] is True
    assert config._config["port"] == 9000
    
    # 2. 嵌套同步
    config.settings.database["host"] = "localhost"
    config.settings.api["version"] = "v2"
    config._sync_config()
    assert config._config["settings"]["database"]["host"] == "localhost"
    assert config._config["settings"]["api"]["version"] == "v2"
    
    # 3. 動態屬性同步
    setattr(config, "new_key", "value")
    config._sync_config()
    assert config._config["new_key"] == "value" 

def test_config_validator_comprehensive():
    """全面測試配置驗證器"""
    config = JSONConfig()
    
    # 1. 基本驗證規則
    validator = ConfigValidator()
    validator.add_rule(
        ValidationRule("port")
        .required()
        .type(int)
        .range(1000, 9999)
    )
    
    # 2. 自定義驗證規則
    validator.add_rule(
        ValidationRule("debug")
        .required()
        .custom(lambda x: isinstance(x, bool), "必須是布爾值")
    )
    
    # 3. 嵌套驗證規則
    validator.add_rule(
        ValidationRule("settings.database.host")
        .required()
        .type(str)
        .pattern(r"^[\w\.-]+$")
    )
    
    # 4. 驗證測試
    config.port = 8080
    config.debug = True
    config.settings.database["host"] = "localhost"
    assert validator.validate(config)
    
    # 5. 錯誤處理
    config.port = "invalid"
    with pytest.raises(ValueError):
        validator.validate(config) 

def test_json_config_advanced():
    """測試 JSON 配置類的進階功能"""
    with tempfile.TemporaryDirectory() as temp_dir:
        config_file = Path(temp_dir) / "config.json"
        
        # 1. 基本序列化
        config = JSONConfig(
            app_name="test_app",
            debug=True,
            port=9000,
            data_path=Path("/test/path"),
            settings={
                "database": {
                    "host": "localhost",
                    "port": 5432
                }
            }
        )
        
        # 1.1 保存配置
        config._config_file_path = config_file
        assert config.save()
        assert config_file.exists()
        
        # 1.2 驗證保存的內容
        saved_data = json.loads(config_file.read_text())
        assert saved_data["app_name"] == "test_app"
        assert saved_data["debug"] is True
        assert saved_data["port"] == 9000
        assert saved_data["data_path"] == {"__path__": "/test/path"}
        assert saved_data["settings"]["database"]["host"] == "localhost"
        
        # 2. 配置加載
        # 2.1 從文件加載
        loaded_config = JSONConfig(config_path=config_file)
        assert loaded_config.app_name == "test_app"
        assert loaded_config.debug is True
        assert loaded_config.port == 9000
        # 統一路徑分隔符後比較
        assert str(loaded_config.data_path).replace('\\', '/') == "/test/path"
        
        # 2.2 重新加載
        config.app_name = "updated_app"
        assert config.save()
        assert loaded_config.reload()
        assert loaded_config.app_name == "updated_app"
        
        # 3. 路徑處理
        # 3.1 Windows 路徑
        config.data_path = Path("C:/Program Files/App")
        assert config.save()
        loaded = JSONConfig(config_path=config_file)
        assert str(loaded.data_path) == "C:/Program Files/App"
        
        # 3.2 相對路徑
        config.data_path = Path("./config/app")
        assert config.save()
        loaded = JSONConfig(config_path=config_file)
        assert str(loaded.data_path) == "./config/app"
        
        # 4. 錯誤處理
        # 4.1 無效的 JSON
        config_file.write_text("invalid json")
        with pytest.raises(ValueError):
            JSONConfig(config_path=config_file)
        
        # 4.2 無效的配置值
        config_file.write_text('{"port": "invalid"}')
        with pytest.raises(ValueError):
            JSONConfig(config_path=config_file)
        
        # 4.3 無配置文件路徑
        config = JSONConfig()
        assert not config.save()  # 沒有配置文件路徑時保存應該失敗
        assert not config.reload()  # 沒有配置文件路徑時重新加載應該失敗 