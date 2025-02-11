import pytest
import asyncio
from pathlib import Path
from src.shared.plugins.manager import PluginManager
from src.shared.plugins.base import PluginConfig

class TestPluginHotReload:
    @pytest.fixture
    async def plugin_manager(self):
        manager = PluginManager()
        await manager.start()
        yield manager
        await manager.stop()
    
    async def test_plugin_reload(self, plugin_manager, tmp_path):
        # 創建臨時插件文件
        plugin_path = tmp_path / "test_plugin.py"
        plugin_code = """
from src.shared.plugins.base import BasePlugin

class TestPlugin(BasePlugin):
    async def initialize(self) -> bool:
        return True
    
    async def execute(self, context):
        return {"result": "v1"}
    
    async def cleanup(self) -> None:
        pass
"""
        plugin_path.write_text(plugin_code)
        
        # 載入插件
        config = PluginConfig(name="test_plugin", version="1.0")
        await plugin_manager.load_plugins(str(tmp_path))
        plugin = await plugin_manager.initialize_plugin("test_plugin", config)
        
        # 執行插件
        result = await plugin_manager.execute_plugin("test_plugin", {})
        assert result["result"] == "v1"
        
        # 修改插件代碼
        new_plugin_code = plugin_code.replace('"v1"', '"v2"')
        plugin_path.write_text(new_plugin_code)
        
        # 等待文件系統事件
        await asyncio.sleep(1)
        
        # 執行更新後的插件
        result = await plugin_manager.execute_plugin("test_plugin", {})
        assert result["result"] == "v2"
    
    async def test_invalid_plugin_reload(self, plugin_manager, tmp_path):
        # 創建臨時插件文件
        plugin_path = tmp_path / "invalid_plugin.py"
        plugin_code = "invalid python code"
        plugin_path.write_text(plugin_code)
        
        # 嘗試載入無效插件
        with pytest.raises(Exception):
            await plugin_manager.reload_plugin(str(plugin_path)) 