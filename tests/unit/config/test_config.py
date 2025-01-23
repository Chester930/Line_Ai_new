import os
import pytest
from src.shared.config.config import Config, Settings

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