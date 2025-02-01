import pytest
from unittest.mock import Mock, patch
from src.shared.plugins.manager import PluginManager
from src.shared.plugins.base import BasePlugin, PluginConfig, PluginError

class MockPlugin(BasePlugin):
    async def initialize(self) -> bool:
        return True
    
    async def execute(self, context: Dict[str, Any]) -> Dict[str, Any]:
        return {"result": "success"}
    
    async def cleanup(self) -> None:
        pass

class TestPluginManager:
    @pytest.fixture
    async def plugin_manager(self):
        manager = PluginManager()
        yield manager
        await manager.cleanup_plugins()
    
    async def test_load_plugins(self, plugin_manager):
        with patch('pkgutil.iter_modules') as mock_iter_modules:
            mock_iter_modules.return_value = [
                (None, "test_plugin", None)
            ]
            
            await plugin_manager.load_plugins()
            assert len(plugin_manager._plugin_classes) == 1
    
    async def test_initialize_plugin(self, plugin_manager):
        plugin_manager._plugin_classes["test"] = MockPlugin
        config = PluginConfig(name="test", version="1.0")
        
        plugin = await plugin_manager.initialize_plugin("test", config)
        assert isinstance(plugin, MockPlugin)
        assert "test" in plugin_manager._plugins
    
    async def test_execute_plugin(self, plugin_manager):
        # 初始化插件
        plugin_manager._plugin_classes["test"] = MockPlugin
        config = PluginConfig(name="test", version="1.0")
        await plugin_manager.initialize_plugin("test", config)
        
        # 執行插件
        result = await plugin_manager.execute_plugin("test", {})
        assert result["result"] == "success"
    
    async def test_plugin_not_found(self, plugin_manager):
        with pytest.raises(PluginError):
            await plugin_manager.initialize_plugin("not_exists", None)
    
    async def test_plugin_disabled(self, plugin_manager):
        plugin_manager._plugin_classes["test"] = MockPlugin
        config = PluginConfig(name="test", version="1.0", enabled=False)
        await plugin_manager.initialize_plugin("test", config)
        
        with pytest.raises(PluginError):
            await plugin_manager.execute_plugin("test", {}) 