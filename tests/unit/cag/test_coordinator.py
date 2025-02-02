import pytest
from src.shared.cag.coordinator import CAGCoordinator, CAGConfig
from src.shared.cag.exceptions import CAGError
from tests.mocks.model_manager import MockModelManager
from src.shared.cag.state import DialogueState
from unittest.mock import AsyncMock
from typing import List, Dict, Any

@pytest.fixture
def mock_rag_system():
    """Mock RAG 系統"""
    class MockRAGSystem:
        async def retrieve(self, query: str) -> List[str]:
            return ["Python is a programming language."]
            
        async def add_document(self, content: str) -> bool:
            return True
            
    return MockRAGSystem()

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

@pytest.mark.asyncio
class TestCAGCoordinator:
    @pytest.fixture
    async def coordinator(self, mock_rag_system, mock_plugin_manager):
        coordinator = await CAGCoordinator.create()
        coordinator.rag_system = mock_rag_system
        coordinator.plugin_manager = mock_plugin_manager
        await coordinator.start()
        try:
            yield coordinator
        finally:
            await coordinator.stop()
            # 確保所有 client sessions 都被關閉
            await coordinator.model.client.close()
    
    async def test_process_message(self, coordinator):
        """測試消息處理流程"""
        # 準備測試數據
        message = "What is Python?"
        context = {"user_id": "test_user"}
        
        # 添加測試文檔
        await coordinator.rag_system.add_document(
            "Python is a high-level programming language."
        )
        
        # 處理消息
        response = await coordinator.process_message(message, context)
        
        # 驗證回應
        assert response is not None
        assert len(response) > 0
        assert "programming language" in response.lower()
        
        # 驗證狀態
        state = await coordinator.state_tracker.get_current_state()
        assert state.state == DialogueState.ACTIVE
        
        # 驗證記憶
        memory = await coordinator.memory_pool.get_memory(
            "context_test_user"
        )
        assert memory is not None

    async def test_error_handling(self, coordinator):
        """測試錯誤處理"""
        # 模擬 RAG 系統錯誤
        coordinator.rag_system.retrieve = AsyncMock(
            side_effect=Exception("RAG error")
        )
        
        # 驗證錯誤處理
        with pytest.raises(CAGError) as exc_info:
            await coordinator.process_message("test", {})
        
        assert "RAG error" in str(exc_info.value)
        
        # 驗證錯誤狀態
        state = await coordinator.state_tracker.get_current_state()
        assert state.state == DialogueState.ERROR
        assert "RAG error" in state.metadata["error"]

    async def test_process_message_old(self):
        """測試舊版消息處理"""
        coordinator = await CAGCoordinator.create()
        try:
            # 處理消息
            response = await coordinator.process_message(
                message="Hello",
                context={"user_id": "test_user"}
            )
            
            # 驗證結果
            assert response is not None
            assert len(response) > 0
            
            # 驗證狀態
            state = await coordinator.state_tracker.get_current_state()
            assert state.state == DialogueState.ACTIVE
            
            # 驗證記憶
            memory = await coordinator.memory_pool.get_memory(
                "context_test_user"
            )
            assert memory is not None
            
        finally:
            await coordinator.stop()
            await coordinator.model.client.close()

    async def test_error_handling_old(self):
        """測試舊版錯誤處理"""
        coordinator = await CAGCoordinator.create()
        try:
            # 模擬錯誤
            coordinator.rag_system.retrieve = AsyncMock(
                side_effect=Exception("Test error")
            )
            
            # 驗證錯誤處理
            with pytest.raises(CAGError) as exc_info:
                await coordinator.process_message(
                    message="Hello",
                    context={"user_id": "test_user"}
                )
            
            assert "Test error" in str(exc_info.value)
            
            # 驗證錯誤狀態
            state = await coordinator.state_tracker.get_current_state()
            assert state.state == DialogueState.ERROR
            assert "Test error" in state.metadata["error"]
            
        finally:
            await coordinator.stop()
            await coordinator.model.client.close() 