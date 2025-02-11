import pytest
from src.shared.config.base import ConfigManager

class TestConfigBase:
    @pytest.fixture
    def config(self):
        return ConfigManager()
        
    def test_config_validation(self, config):
        """測試配置驗證"""
        # 測試必要字段
        with pytest.raises(ValueError):
            config.validate({})
            
        # 測試有效配置
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
        assert config.validate(valid_config) 