import os
import pytest
from src.shared.config.config import Config, Settings
from pathlib import Path
from src.shared.config.manager import ConfigManager
from src.shared.config.validator import ConfigValidator
from src.shared.config.json_config import JSONConfig

@pytest.fixture
def test_config():
    """配置測試夾具"""
    config = Config()
    # 保存原始環境變量
    original_env = {
        'LINE_CHANNEL_SECRET': os.getenv('LINE_CHANNEL_SECRET'),
        'LINE_CHANNEL_ACCESS_TOKEN': os.getenv('LINE_CHANNEL_ACCESS_TOKEN'),
        'DATABASE_URL': os.getenv('DATABASE_URL'),
        'APP_NAME': os.getenv('APP_NAME')
    }
    
    # 設置測試環境變量
    os.environ['LINE_CHANNEL_SECRET'] = 'test_secret'
    os.environ['LINE_CHANNEL_ACCESS_TOKEN'] = 'test_token'
    os.environ['DATABASE_URL'] = 'sqlite:///test.db'
    
    yield config
    
    # 恢復原始環境變量
    for key, value in original_env.items():
        if value is None:
            os.environ.pop(key, None)
        else:
            os.environ[key] = value

def test_config_singleton():
    """測試配置單例模式"""
    config1 = Config()
    config2 = Config()
    assert config1 is config2

def test_settings_loading():
    """測試設置加載"""
    config = Config()
    settings = config.settings
    assert isinstance(settings, Settings)
    assert settings.app_name == "LINE AI Assistant Test"
    assert settings.line_channel_secret == "test_secret"
    assert settings.line_channel_access_token == "test_token"

def test_config_get_method():
    """測試配置獲取方法"""
    config = Config()
    assert config.get('line.channel_secret') == 'test_secret'
    assert config.get('nonexistent', 'default') == 'default'

def test_environment_variables(test_config):
    """測試環境變量加載"""
    assert test_config.settings.line_channel_secret == "test_secret"
    assert test_config.settings.line_channel_access_token == "test_token"
    assert test_config.settings.database_url == "sqlite:///test.db"

def test_config_loading(test_config):
    """測試配置加載"""
    assert test_config.get('app_name') == 'LINE AI Assistant Test'
    assert test_config.get('line.channel_secret') == 'test_secret'
    assert test_config.get('database.url') == 'sqlite:///test.db'

def test_config_default_values():
    """測試默認值"""
    config = Config()
    assert config.settings.debug is True
    assert config.settings.log_level == "INFO"

def test_config_merge():
    """測試配置合併"""
    config = Config()
    target = {'a': {'b': 1}}
    source = {'a': {'c': 2}}
    config._merge_config(target, source)
    assert target == {'a': {'b': 1, 'c': 2}}

def test_config_reload(test_config):
    """測試配置重載"""
    original_secret = test_config.get('line.channel_secret')
    os.environ['LINE_CHANNEL_SECRET'] = 'new_secret'
    test_config.reload()
    assert test_config.get('line.channel_secret') == 'new_secret'
    # 恢復原始值
    os.environ['LINE_CHANNEL_SECRET'] = original_secret 

@pytest.fixture
def test_settings():
    """測試設置"""
    return Settings(
        GOOGLE_API_KEY="test_key",
        LINE_CHANNEL_SECRET="test_secret",
        LINE_CHANNEL_ACCESS_TOKEN="test_token",
        DEBUG=True
    )

@pytest.fixture
def config_manager(test_settings):
    """測試配置管理器"""
    return ConfigManager()

def test_settings_validation(test_settings):
    """測試設置驗證"""
    validator = ConfigValidator(settings=test_settings)
    result = validator.validate_all()
    assert "success" in result

def test_model_config(config_manager):
    """測試模型配置"""
    config = config_manager.get_model_config("gemini")
    assert "api_key" in config
    assert "timeout" in config
    assert "max_retries" in config

def test_directory_creation(config_manager):
    """測試目錄創建"""
    assert config_manager.settings.LOG_DIR.exists()
    assert (config_manager.settings.BASE_DIR / "data").exists()
    assert (config_manager.settings.BASE_DIR / "temp").exists()

def test_config_update(config_manager):
    """測試配置更新"""
    config_manager.update_setting("DEBUG", False)
    assert not config_manager.debug_mode

def test_invalid_config_update(config_manager):
    """測試無效配置更新"""
    with pytest.raises(ValueError):
        config_manager.update_setting("INVALID_KEY", "value")

def test_env_template_generation(config_manager):
    """測試環境變量模板生成"""
    template = config_manager.get_env_file_template()
    assert "GOOGLE_API_KEY" in template
    assert "LINE_CHANNEL_SECRET" in template 

@pytest.fixture
def temp_config_file(tmp_path):
    """臨時配置文件"""
    return tmp_path / "test_config.json"

@pytest.fixture
def json_config(temp_config_file):
    """JSON 配置"""
    return JSONConfig(temp_config_file)

@pytest.fixture
def config_manager(tmp_path):
    """配置管理器"""
    return ConfigManager(tmp_path)

def test_config_basic_operations(json_config):
    """測試基本配置操作"""
    # 設置值
    assert json_config.set("test_key", "test_value")
    assert json_config.get("test_key") == "test_value"
    
    # 設置嵌套值
    assert json_config.set("nested.key", "nested_value")
    assert json_config.get("nested.key") == "nested_value"
    
    # 獲取默認值
    assert json_config.get("non_existent", "default") == "default"
    
    # 更新配置
    assert json_config.update({"new_key": "new_value"})
    assert json_config.get("new_key") == "new_value"

def test_config_save_load(json_config):
    """測試配置保存和載入"""
    # 設置並保存
    json_config.set("test_key", "test_value")
    assert json_config.save()
    
    # 創建新實例載入
    new_config = JSONConfig(json_config.config_path)
    assert new_config.get("test_key") == "test_value"

def test_config_manager(config_manager):
    """測試配置管理器"""
    # 獲取不同配置
    ai_config = config_manager.get_ai_config()
    app_config = config_manager.get_app_config()
    
    # 設置配置值
    ai_config.set("openai.api_key", "test_key")
    app_config.set("debug", True)
    
    # 保存所有配置
    assert config_manager.save_all()
    
    # 重新載入配置
    config_manager.reload_all()
    
    # 驗證值保持不變
    ai_config = config_manager.get_ai_config()
    app_config = config_manager.get_app_config()
    assert ai_config.get("openai.api_key") == "test_key"
    assert app_config.get("debug") is True

def test_config_file_creation(tmp_path):
    """測試配置文件創建"""
    config_path = tmp_path / "new_config.json"
    config = JSONConfig(config_path)
    
    # 確認文件被創建
    assert config_path.exists()
    
    # 確認是有效的 JSON
    content = config_path.read_text()
    assert content == "{}" 