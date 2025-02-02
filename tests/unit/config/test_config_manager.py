import pytest
import os
from pathlib import Path
from src.shared.config.manager import ConfigManager

@pytest.fixture
def config_dir(tmp_path):
    return tmp_path / "config"

@pytest.fixture
def config_manager(config_dir):
    return ConfigManager(config_dir=config_dir)

class TestConfigManager:
    def test_get_line_config(self, config_manager, monkeypatch):
        # 模擬環境變量
        monkeypatch.setenv("LINE_CHANNEL_SECRET", "test_secret")
        monkeypatch.setenv("LINE_CHANNEL_ACCESS_TOKEN", "test_token")
        
        config = config_manager.get_line_config()
        assert config["channel_secret"] == "test_secret"
        assert config["channel_access_token"] == "test_token"
        
    def test_get_config_value(self, config_manager, monkeypatch):
        monkeypatch.setenv("TEST_KEY", "test_value")
        assert config_manager.get("TEST_KEY") == "test_value"
        assert config_manager.get("NON_EXISTENT_KEY", "default") == "default"

    def test_environment_handling(self, config_manager):
        assert config_manager.get_environment() == "test"  # 由 conftest.py 設置 