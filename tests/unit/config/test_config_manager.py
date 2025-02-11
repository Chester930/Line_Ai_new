import pytest
import os
from pathlib import Path
from src.shared.config.manager import ConfigManager
from src.shared.config.validator import ValidationError
import json

@pytest.fixture
def config_dir(tmp_path):
    return tmp_path / "config"

@pytest.fixture
def config_manager(tmp_path):
    """使用臨時目錄作為配置目錄"""
    os.environ["ENV"] = "test"  # 設置測試環境
    manager = ConfigManager(config_dir=tmp_path)
    yield manager
    os.environ.pop("ENV", None)  # 清理環境變量

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
        """測試環境處理"""
        assert config_manager.get_environment() == "test"

    @pytest.mark.asyncio
    async def test_reload_config(self, config_manager, tmp_path):
        """測試重新載入配置"""
        config_path = tmp_path / "test.json"
        config = {
            "test_key": "test_value"
        }
        
        # 保存初始配置
        await config_manager.save_config("test.json", config)
        
        # 修改配置
        config["test_key"] = "new_value"
        await config_manager.save_config("test.json", config)
        
        # 重新載入
        assert await config_manager.reload_config("test.json")
        loaded = await config_manager.get_config("test.json")
        assert loaded["test_key"] == "new_value"

    @pytest.mark.asyncio
    async def test_reload_all(self, config_manager, tmp_path):
        """測試重新載入所有配置"""
        configs = {
            "config1.json": {"key1": "value1"},
            "config2.json": {"key2": "value2"}
        }
        
        # 保存配置
        for name, data in configs.items():
            await config_manager.save_config(name, data)
        
        # 修改所有配置
        for name, data in configs.items():
            data["new_key"] = "new_value"
            await config_manager.save_config(name, data)
        
        # 重新載入所有
        assert await config_manager.reload_all()
        
        # 驗證更新
        for name in configs:
            loaded = await config_manager.get_config(name)
            assert loaded["new_key"] == "new_value"

    def test_validate_config_schema(self, config_manager):
        """測試配置模式驗證"""
        from pydantic import BaseModel
        
        class TestConfig(BaseModel):
            key: str
            value: int
            
        valid_config = {
            "key": "test",
            "value": 123
        }
        
        invalid_config = {
            "key": "test",
            "value": "not_a_number"
        }
        
        # 驗證有效配置
        assert config_manager.validate_config_schema(valid_config, TestConfig)
        
        # 驗證無效配置
        with pytest.raises(ValidationError):
            config_manager.validate_config_schema(invalid_config, TestConfig)

    @pytest.mark.asyncio
    async def test_environment_switching(self, config_manager, tmp_path):
        """測試環境切換"""
        # 保存開發環境配置
        dev_config = {"env": "development"}
        await config_manager.save_config("config.json", dev_config)
        
        # 保存測試環境配置
        test_config = {"env": "test"}
        await config_manager.set_environment("test")
        await config_manager.save_config("config.json", test_config)
        
        # 驗證環境切換
        assert config_manager.get_environment() == "test"
        loaded = await config_manager.get_config("config.json")
        assert loaded["env"] == "test"

    @pytest.mark.asyncio
    async def test_save_all(self, config_manager, tmp_path):
        """測試保存所有配置"""
        configs = {
            "config1.json": {"key1": "value1"},
            "config2.json": {"key2": "value2"}
        }
        
        # 保存配置
        for name, data in configs.items():
            await config_manager.save_config(name, data)
            config_manager.configs[name] = data.copy()  # 使用 copy 避免引用問題
        
        # 修改所有配置
        for name in configs:
            config_manager.configs[name]["new_key"] = "new_value"
        
        # 保存所有
        assert await config_manager.save_all()
        
        # 驗證更新
        for name in configs:
            loaded = await config_manager.get_config(name)
            assert loaded["new_key"] == "new_value"

@pytest.mark.asyncio
async def test_config_manager(tmp_path):
    """測試配置管理器"""
    config_dir = tmp_path / "config"
    config_dir.mkdir(exist_ok=True)
    
    try:
        # 初始化配置管理器
        manager = ConfigManager(config_dir=config_dir)
        
        # 測試配置加載
        config = {
            "test_key": "test_value",
            "nested": {"key": "value"}
        }
        await manager.save_config("test.json", config)
        loaded = await manager.load_config("test.json")
        assert loaded["test_key"] == "test_value"
        
        # 測試配置驗證
        invalid_config = {"invalid_key": None}
        with pytest.raises(ValidationError):
            await manager.validate_config(invalid_config)
        
        # 測試配置更新
        update = {"test_key": "new_value"}
        await manager.update_config("test.json", update)
        updated = await manager.get_config("test.json")
        assert updated["test_key"] == "new_value"
        
        # 測試配置刪除
        await manager.delete_config("test.json")
        with pytest.raises(FileNotFoundError):
            await manager.get_config("test.json")
            
    finally:
        # 清理測試文件
        if config_dir.exists():
            import shutil
            shutil.rmtree(config_dir, ignore_errors=True) 