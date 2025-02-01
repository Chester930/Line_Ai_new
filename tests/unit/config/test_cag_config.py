import pytest
from pathlib import Path
import json
from src.shared.config.cag_config import ConfigManager, CAGSystemConfig, ModelConfig

class TestConfigManager:
    def setup_method(self):
        self.test_config_path = "tests/data/test_config.json"
        self.config_manager = ConfigManager(self.test_config_path)
    
    def teardown_method(self):
        # 清理測試配置文件
        config_file = Path(self.test_config_path)
        if config_file.exists():
            config_file.unlink()
    
    def test_create_default_config(self):
        config = self.config_manager.load_config()
        
        assert isinstance(config, CAGSystemConfig)
        assert config.max_context_length == 2000
        assert config.memory_ttl == 3600
        assert "gemini" in config.models
    
    def test_save_and_load_config(self):
        # 創建測試配置
        test_config = CAGSystemConfig(
            max_context_length=1500,
            memory_ttl=1800,
            models={
                "test_model": ModelConfig(
                    name="test_model",
                    api_key="test_key",
                    max_tokens=500
                )
            }
        )
        
        # 保存配置
        self.config_manager.config = test_config
        self.config_manager.save_config()
        
        # 重新加載配置
        new_config = self.config_manager.load_config()
        
        # 驗證配置
        assert new_config.max_context_length == 1500
        assert new_config.memory_ttl == 1800
        assert "test_model" in new_config.models
        assert new_config.models["test_model"].api_key == "test_key"
    
    def test_invalid_config_file(self):
        # 創建無效的配置文件
        config_file = Path(self.test_config_path)
        config_file.parent.mkdir(parents=True, exist_ok=True)
        config_file.write_text("invalid json")
        
        # 應該返回默認配置
        config = self.config_manager.load_config()
        assert isinstance(config, CAGSystemConfig)
        assert config.max_context_length == 2000 