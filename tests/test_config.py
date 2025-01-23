import pytest
from src.shared.config.config import config

def test_config_loading():
    assert config.get('app.name') == 'LINE AI Assistant'
    assert config.get('app.version') == '1.0.0'
    assert config.get('app.debug') is True

def test_config_default_value():
    assert config.get('non.existent.key', 'default') == 'default' 