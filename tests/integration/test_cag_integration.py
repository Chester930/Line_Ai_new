import pytest
from src.shared.cag.coordinator import CAGCoordinator
from src.shared.cag.state import DialogueState

@pytest.mark.asyncio
class TestCAGIntegration:
    async def test_end_to_end_flow(self, coordinator):
        """測試完整的端到端流程"""
        try:
            # 1. 添加測試文檔
            await coordinator.rag_system.add_document(
                "Python is a high-level programming language."
            )
            
            # 2. 處理消息
            response = await coordinator.process_message(
                "Tell me about Python",
                {"user_id": "test_user"}
            )
            
            # 3. 驗證結果
            assert response == "This is a mock response"
            
            # 4. 驗證狀態
            state = await coordinator.state_tracker.get_current_state()
            assert state.state == DialogueState.ACTIVE
            
            # 5. 驗證記憶
            memory = await coordinator.memory_pool.get_memory(
                "context_test_user"
            )
            assert memory is not None
            
        finally:
            await coordinator.stop()
            if hasattr(coordinator, 'model'):
                await coordinator.model.close()