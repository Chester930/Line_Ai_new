import pytest
from pathlib import Path
import json
from src.shared.config.plugin_config import PluginConfigManager, PluginSettings

class TestPluginConfigManager:
    def setup_method(self):
        self.test_config_path = "tests/data/test_plugins_config.json"
        self.config_manager = PluginConfigManager(self.test_config_path)
    
    def teardown_method(self):
        config_file = Path(self.test_config_path)
        if config_file.exists():
            config_file.unlink()
    
    def test_load_configs(self):
        # 創建測試配置文件
        config_data = {
            "plugins": {
                "test_plugin": {
                    "enabled": True,
                    "version": "1.0",
                    "settings": {
                        "api_key": "test_key"
                    }
                }
            }
        }
        
        config_file = Path(self.test_config_path)
        config_file.parent.mkdir(parents=True, exist_ok=True)
        with open(config_file, 'w') as f:
            json.dump(config_data, f)
        
        # 載入配置
        self.config_manager.load_configs()
        
        # 驗證配置
        assert "test_plugin" in self.config_manager.configs
        plugin_config = self.config_manager.configs["test_plugin"]
        assert plugin_config.enabled
        assert plugin_config.version == "1.0"
        assert plugin_config.settings["api_key"] == "test_key"
    
    def test_save_configs(self):
        # 設置測試配置
        self.config_manager.configs["test_plugin"] = PluginSettings(
            enabled=True,
            version="1.0",
            settings={"api_key": "test_key"}
        )
        
        # 保存配置
        self.config_manager.save_configs()
        
        # 驗證保存的文件
        config_file = Path(self.test_config_path)
        assert config_file.exists()
        
        with open(config_file, 'r') as f:
            saved_data = json.load(f)
        
        assert "test_plugin" in saved_data["plugins"]
        plugin_data = saved_data["plugins"]["test_plugin"]
        assert plugin_data["enabled"]
        assert plugin_data["version"] == "1.0"
        assert plugin_data["settings"]["api_key"] == "test_key" 