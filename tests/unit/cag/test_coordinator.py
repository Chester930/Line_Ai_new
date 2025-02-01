import pytest
from src.shared.cag.coordinator import CAGCoordinator, CAGConfig
from src.shared.cag.exceptions import CAGError
from tests.mocks.model_manager import MockModelManager

@pytest.mark.asyncio
class TestCAGCoordinator:
    async def test_process_message(self):
        # 初始化協調器
        model_manager = MockModelManager()
        coordinator = CAGCoordinator(model_manager)
        
        # 處理消息
        result = await coordinator.process_message(
            message="Hello",
            user_id="test_user"
        )
        
        # 驗證結果
        assert result.content == "This is a mock response"
        
        # 驗證狀態
        current_state = await coordinator.state_tracker.get_current_state()
        assert current_state.state.value == "active"
        assert current_state.metadata["user_id"] == "test_user"
        
        # 驗證上下文
        assert len(coordinator.context_manager.current_context.messages) == 1
        
        # 驗證記憶
        memory = await coordinator.memory_pool.get_memory("context_test_user")
        assert memory is not None
    
    async def test_error_handling(self):
        # 使用會產生錯誤的模擬模型管理器
        model_manager = MockModelManager(raise_error=True)
        coordinator = CAGCoordinator(model_manager)
        
        # 驗證錯誤處理
        with pytest.raises(CAGError):
            await coordinator.process_message(
                message="Hello",
                user_id="test_user"
            )
        
        # 驗證錯誤狀態
        current_state = await coordinator.state_tracker.get_current_state()
        assert current_state.state.value == "error" 