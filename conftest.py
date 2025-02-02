import os
import sys
import pytest
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock
from typing import Dict, Any

# 只導入測試需要的組件
from src.shared.cag.context import ContextManager
from src.shared.cag.memory import MemoryPool
from src.shared.cag.state import StateTracker
from src.shared.ai.models.gemini import GeminiConfig
from src.shared.cag.coordinator import CAGCoordinator

@pytest.fixture(autouse=True)
def setup_test_env(tmp_path):
    """設置測試環境"""
    os.environ["APP_ENV"] = "test"
    os.environ["CONFIG_DIR"] = str(tmp_path / "config")
    
    # 創建測試配置目錄
    config_dir = Path(os.environ["CONFIG_DIR"])
    config_dir.mkdir(parents=True, exist_ok=True)
    
    yield
    
    # 清理測試文件
    if config_dir.exists():
        for f in config_dir.glob("*.json"):
            f.unlink()

@pytest.fixture
def context_manager():
    """上下文管理器"""
    return ContextManager(max_context_length=2000)

@pytest.fixture
def memory_pool():
    """記憶池"""
    return MemoryPool()

@pytest.fixture
def state_tracker():
    """狀態追蹤器"""
    return StateTracker()

@pytest.fixture
async def coordinator():
    """共用的 CAG 協調器 fixture"""
    coordinator = await CAGCoordinator.create()
    try:
        yield coordinator
    finally:
        await coordinator.stop()
        if hasattr(coordinator, 'model'):
            await coordinator.model.client.close()

@pytest.fixture
def mock_plugin_manager():
    """Mock 插件管理器"""
    class MockPluginManager:
        def __init__(self):
            self._plugins = {}
            
        async def process(self, message: str) -> Dict[str, Any]:
            return {"test_plugin": {"result": "test"}}
            
        async def start_watching(self, *args):
            pass
            
        async def stop_watching(self):
            pass
            
        async def cleanup_plugins(self):
            pass
            
        async def load_plugins(self):
            pass
            
        async def initialize_plugin(self, name: str, config: Any):
            pass
    
    return MockPluginManager() 