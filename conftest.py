import os
import sys
import pytest
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock

# 只導入測試需要的組件
from src.shared.cag.context import ContextManager
from src.shared.cag.memory import MemoryPool
from src.shared.cag.state import StateTracker

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