import pytest
import os
from src.shared.config.manager import ConfigManager

@pytest.mark.asyncio
async def test_config_loading(self):
    """測試配置加載"""
    config = ConfigManager()
    
    # 測試環境變量加載
    os.environ["TEST_VAR"] = "test_value"
    assert config.get("TEST_VAR") == "test_value"
    
    # 測試配置文件加載
    config.load_from_file("config.yaml")
    assert config.get("database.url") is not None
    
    # 測試配置合併
    config.merge({
        "new_key": "new_value"
    })
    assert config.get("new_key") == "new_value" 