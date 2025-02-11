import os
import sys
import pytest
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, create_autospec
from typing import Dict, Any, List, Optional
import json
import asyncio

# 只導入測試需要的組件
from src.shared.cag.context import ContextManager
from src.shared.cag.memory import MemoryPool
from src.shared.cag.state import StateTracker
from src.shared.cag.coordinator import CAGCoordinator
from src.shared.cag.generator import ResponseGenerator

@pytest.fixture(autouse=True)
def setup_test_env(tmp_path):
    """設置測試環境"""
    os.environ["APP_ENV"] = "test"
    os.environ["CONFIG_DIR"] = str(tmp_path / "config")
    
    # 創建測試配置目錄
    config_dir = Path(os.environ["CONFIG_DIR"])
    config_dir.mkdir(parents=True, exist_ok=True)
    
    # 創建測試 fixtures 目錄
    fixtures_dir = Path("tests/fixtures/config")
    fixtures_dir.mkdir(parents=True, exist_ok=True)
    
    yield
    
    # 清理測試文件
    if config_dir.exists():
        for f in config_dir.glob("*.json"):
            f.unlink()
    if fixtures_dir.exists():
        for f in fixtures_dir.glob("*.json"):
            f.unlink()
        fixtures_dir.rmdir()

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
def test_config():
    """測試配置"""
    return {
        "models": {
            "gemini": {
                "api_key": "test_key",
                "name": "gemini",
                "model_name": "gemini-pro"
            }
        },
        "max_context_length": 2000,
        "memory_ttl": 3600,
        "enable_state_tracking": True,
        "plugins": {
            "web_search": {
                "enabled": True,
                "version": "1.0",
                "settings": {}
            },
            "image_analyzer": {
                "enabled": True,
                "version": "1.0",
                "settings": {}
            }
        }
    }

@pytest.fixture
async def coordinator(mock_gemini_model, mock_rag_system, mock_plugin_manager, test_config):
    """共用的 CAG 協調器 fixture"""
    coordinator = None
    config_path = "tests/fixtures/config/test_config.json"
    
    try:
        # 創建測試配置文件
        os.makedirs(os.path.dirname(config_path), exist_ok=True)
        with open(config_path, "w", encoding="utf-8") as f:
            json.dump(test_config, f, indent=4)
            
        coordinator = await CAGCoordinator.create(config_path=config_path)
        
        # 替換為 mock 組件
        coordinator.model = mock_gemini_model
        coordinator.rag_system = mock_rag_system
        coordinator.plugin_manager = mock_plugin_manager
        
        # 重新初始化 generator 以使用 mock model
        coordinator.generator = ResponseGenerator(mock_gemini_model)
        
        await coordinator.start()
        
        yield coordinator
        
    finally:
        if coordinator:
            try:
                await coordinator.stop()
            except:
                pass
            try:
                if hasattr(coordinator, 'model'):
                    await coordinator.model.close()
            except:
                pass
        
        if os.path.exists(config_path):
            os.remove(config_path)

@pytest.fixture
def mock_plugin_manager():
    """Mock 插件管理器"""
    manager = AsyncMock()
    manager.process.return_value = {"test_plugin": {"result": "test"}}
    return manager

@pytest.fixture
def mock_gemini_model():
    """Mock Gemini 模型"""
    class MockResponse:
        def __init__(self, content):
            self.content = content
    
    class MockGeminiModel:
        async def generate(self, prompt, context=None, **kwargs):
            return MockResponse("This is a mock response")
            
        async def close(self):
            pass
            
        async def generate_stream(self, prompt, context=None, **kwargs):
            return MockResponse("Streaming response")
            
        async def count_tokens(self, text):
            return 10
            
        async def validate(self):
            return True
            
    return MockGeminiModel()

@pytest.fixture
def mock_rag_system():
    """Mock RAG 系統"""
    system = AsyncMock()
    system.retrieve.return_value = ["Python is a programming language."]
    system.add_document.return_value = True
    return system 