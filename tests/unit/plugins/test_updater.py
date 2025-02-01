import pytest
from unittest.mock import Mock, patch, AsyncMock
from pathlib import Path
import aiohttp
from src.shared.plugins.updater import PluginUpdater
from src.shared.plugins.version import PluginVersion

class TestPluginUpdater:
    @pytest.fixture
    async def updater(self):
        plugin_manager = Mock()
        version_manager = Mock()
        config_manager = Mock()
        
        updater = PluginUpdater(
            plugin_manager,
            version_manager,
            config_manager
        )
        yield updater
        await updater.close()
    
    @pytest.mark.asyncio
    async def test_check_updates(self, updater):
        # 模擬遠程版本信息
        remote_versions = {
            "test_plugin": {
                "version": "1.1.0",
                "description": "Test Plugin",
                "author": "Test Author",
                "dependencies": {},
                "requirements": [],
                "changes": "Test changes"
            }
        }
        
        # 模擬配置
        updater.config_manager.configs = {
            "test_plugin": Mock(version="1.0.0")
        }
        
        # 模擬 HTTP 響應
        mock_response = Mock()
        mock_response.status = 200
        mock_response.json = AsyncMock(return_value=remote_versions)
        
        # 模擬 aiohttp session
        mock_session = AsyncMock()
        mock_session.get.return_value.__aenter__.return_value = mock_response
        updater.session = mock_session
        
        # 執行檢查
        updates = await updater.check_updates()
        
        # 驗證結果
        assert "test_plugin" in updates
        assert updates["test_plugin"].version == "1.1.0"
    
    @pytest.mark.asyncio
    async def test_update_plugin(self, updater, tmp_path):
        # 模擬插件配置
        config = Mock(version="1.0.0")
        updater.config_manager.get_plugin_config.return_value = config
        
        # 模擬升級路徑
        upgrade_version = PluginVersion(
            version="1.1.0",
            description="Test Plugin",
            author="Test Author",
            dependencies={},
            requirements=[],
            changes="Test changes"
        )
        updater.version_manager.get_upgrade_path.return_value = [upgrade_version]
        
        # 模擬下載更新包
        mock_response = Mock()
        mock_response.status = 200
        mock_response.read = AsyncMock(return_value=b"test data")
        
        mock_session = AsyncMock()
        mock_session.get.return_value.__aenter__.return_value = mock_response
        updater.session = mock_session
        
        # 執行更新
        success = await updater.update_plugin("test_plugin")
        
        # 驗證結果
        assert success
        assert config.version == "1.1.0"
        updater.plugin_manager.reload_plugin.assert_called_once() 