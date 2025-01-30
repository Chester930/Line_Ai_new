import pytest
import json
import tempfile
from pathlib import Path
from typing import Dict, Optional
import os
import shutil
from pydantic import Field

from src.shared.config.json_config import JSONConfig, PathEncoder
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
    TestConfig = get_test_config()
    config = TestConfig(config_path=config_file, api_key=None)
    
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
    
    TestConfig = get_test_config()
    with pytest.raises(json.JSONDecodeError):
        TestConfig(config_path=invalid_file)

def test_load_nonexistent_file(tmp_path):
    """測試加載不存在的文件"""
    nonexistent_file = tmp_path / "nonexistent.json"
    
    TestConfig = get_test_config()
    config = TestConfig(config_path=nonexistent_file)
    
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
    TestConfig = get_test_config()
    
    # 創建並修改配置
    config = TestConfig(config_path=config_file)
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
    TestConfig = get_test_config()
    config = TestConfig(config_path=config_file)
    
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
    TestConfig = get_test_config()
    config = TestConfig(config_path=config_file)
    
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
    TestConfig = get_test_config()
    
    # 使用字符串路徑創建配置
    config = TestConfig(config_path=str(config_file))
    assert isinstance(config.config_path, Path)
    
    # 使用 Path 對象創建配置
    config = TestConfig(config_path=config_file)
    assert isinstance(config.config_path, Path)

def test_config_directory_creation(tmp_path):
    """測試配置目錄創建"""
    config_dir = tmp_path / "config" / "nested"
    config_file = config_dir / "config.json"
    
    TestConfig = get_test_config()
    config = TestConfig(config_path=config_file)
    
    # 保存配置應該創建目錄
    assert config.save()
    assert config_file.parent.exists()
    assert config_file.exists()

def test_config_reload(config_file):
    """測試重新加載配置"""
    TestConfig = get_test_config()
    config = TestConfig(config_path=config_file)
    
    # 修改配置文件
    data = json.loads(config_file.read_text())
    data["app_name"] = "modified_app"
    config_file.write_text(json.dumps(data))
    
    # 重新加載
    config.reload()
    assert config.app_name == "modified_app"

def test_path_encoder():
    """測試 Path 對象的 JSON 編碼"""
    # 創建測試路徑
    test_path = Path("/test/path")
    test_data = {"path": test_path}
    
    # 使用 PathEncoder 編碼
    encoded = json.dumps(test_data, cls=PathEncoder)
    decoded = json.loads(encoded)
    
    # 驗證結果
    assert decoded["path"] == str(test_path)
    
    # 測試非 Path 對象
    test_data = {"number": 42, "string": "test"}
    encoded = json.dumps(test_data, cls=PathEncoder)
    decoded = json.loads(encoded)
    
    assert decoded == test_data

def test_path_encoder_with_nested_paths():
    """測試嵌套 Path 對象的 JSON 編碼"""
    # 創建測試數據
    test_data = {
        "paths": [
            Path("/path1"),
            Path("/path2")
        ],
        "nested": {
            "path": Path("/nested/path")
        }
    }
    
    # 使用 PathEncoder 編碼
    encoded = json.dumps(test_data, cls=PathEncoder)
    decoded = json.loads(encoded)
    
    # 驗證結果
    assert decoded["paths"] == [str(p) for p in test_data["paths"]]
    assert decoded["nested"]["path"] == str(test_data["nested"]["path"])

def test_config_save_without_path():
    """測試沒有配置路徑時的保存操作"""
    TestConfig = get_test_config()
    config = TestConfig()  # 不提供配置路徑
    
    # 保存應該失敗
    assert not config.save()

def test_config_update_with_invalid_data():
    """測試使用無效數據更新配置"""
    TestConfig = get_test_config()
    config = TestConfig()
    
    # 使用無效的端口值更新
    with pytest.raises(ValueError):
        config.update({"port": "invalid"})

def test_config_reload_without_path():
    """測試沒有配置路徑時的重新加載操作"""
    TestConfig = get_test_config()
    config = TestConfig()
    
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
    TestConfig = get_test_config()
    config = TestConfig(config_path=config_file)
    
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

def test_path_encoder():
    """測試路徑編碼器"""
    encoder = PathEncoder()
    test_path = Path("/test/path")
    
    # 測試編碼 Path 對象
    assert encoder.default(test_path) == str(test_path)
    
    # 測試編碼字典
    data = {"path": test_path}
    assert encoder.default(data) == {"path": str(test_path)}
    
    # 測試編碼列表
    data = [test_path]
    assert encoder.default(data) == [str(test_path)]

def test_config_get_set_operations(tmp_path):
    """測試配置的 get/set 操作"""
    config_file = tmp_path / "config.json"
    TestConfig = get_test_config()
    config = TestConfig(config_path=config_file)
    
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
    TestConfig = get_test_config()
    config = TestConfig(config_path=config_file)
    
    # 測試布爾值轉換
    os.environ["TEST_DEBUG"] = "true"
    config = TestConfig(config_path=config_file)
    assert config.debug is True
    
    # 測試整數轉換
    os.environ["TEST_PORT"] = "9000"
    config = TestConfig(config_path=config_file)
    assert config.port == 9000
    
    # 測試路徑轉換
    test_path = "/test/path"
    os.environ["TEST_DATA_PATH"] = test_path
    config = TestConfig(config_path=config_file)
    assert isinstance(config.data_path, Path)
    assert str(config.data_path) == test_path
    
    # 清理環境變量
    del os.environ["TEST_DEBUG"]
    del os.environ["TEST_PORT"]
    del os.environ["TEST_DATA_PATH"]

def test_config_nested_settings(tmp_path):
    """測試嵌套設置的處理"""
    config_file = tmp_path / "config.json"
    TestConfig = get_test_config()
    
    # 設置嵌套環境變量
    os.environ["TEST_SETTINGS__DATABASE__HOST"] = "localhost"
    os.environ["TEST_SETTINGS__DATABASE__PORT"] = "5432"
    os.environ["TEST_SETTINGS__API__VERSION"] = "v1"
    
    config = TestConfig(config_path=config_file)
    
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
    TestConfig = get_test_config()
    config = TestConfig(config_path=config_file)
    
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
    
    TestConfig = get_test_config()
    config = TestConfig(
        config_path=config_file,
        app_name="override_app",
        settings={"api": {"key": "test"}}
    )
    
    # 驗證合併結果
    assert config.app_name == "override_app"  # 參數覆蓋文件
    assert config.settings["database"]["host"] == "localhost"  # 保留文件中的設置
    assert config.settings["api"]["key"] == "test"  # 添加新的設置

def test_config_error_handling(tmp_path):
    """測試錯誤處理"""
    config_file = tmp_path / "config.json"
    TestConfig = get_test_config()
    config = TestConfig(config_path=config_file)
    
    # 測試無效的 JSON 更新
    with pytest.raises(ValueError):
        config.update({"port": "invalid"})
    
    # 測試文件訪問錯誤
    config.config_path = Path("/nonexistent/path/config.json")
    assert not config.save()
    
    # 測試無效的配置路徑
    with pytest.raises(ValueError):
        config.config_path = "invalid_path"  # 應該是 Path 對象

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
    
    TestConfig = get_test_config()
    config = TestConfig(
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