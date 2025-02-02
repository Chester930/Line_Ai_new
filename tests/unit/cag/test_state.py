import pytest
from datetime import datetime
from src.shared.cag.state import StateTracker, DialogueState, StateData

@pytest.mark.asyncio
class TestStateTracker:
    @pytest.fixture
    def state_tracker(self):
        return StateTracker()
    
    async def test_set_state(self, state_tracker):
        """測試設置狀態"""
        metadata = {"user_id": "test_user"}
        await state_tracker.set_state(DialogueState.ACTIVE, metadata)
        
        current_state = await state_tracker.get_current_state()
        assert current_state is not None
        assert current_state.state == DialogueState.ACTIVE
        assert current_state.metadata == metadata
        assert isinstance(current_state.updated_at, datetime)
    
    async def test_state_history(self, state_tracker):
        """測試狀態歷史"""
        # 設置多個狀態
        states = [
            (DialogueState.INIT, {"init": True}),
            (DialogueState.ACTIVE, {"active": True}),
            (DialogueState.WAITING, {"waiting": True})
        ]
        
        for state, metadata in states:
            await state_tracker.set_state(state, metadata)
        
        # 檢查歷史記錄
        history = await state_tracker.get_state_history()
        assert len(history) == len(states) - 1  # 當前狀態不在歷史中
        
        # 檢查最後一個狀態
        current = await state_tracker.get_current_state()
        assert current.state == DialogueState.WAITING
        assert current.metadata == {"waiting": True}
    
    async def test_state_transitions(self, state_tracker):
        """測試狀態轉換"""
        transitions = [
            (DialogueState.INIT, "初始化"),
            (DialogueState.PROCESSING, "處理中"),
            (DialogueState.ACTIVE, "對話中"),
            (DialogueState.WAITING, "等待回應"),
            (DialogueState.ENDED, "對話結束")
        ]
        
        for state, message in transitions:
            await state_tracker.set_state(state, {"message": message})
            current = await state_tracker.get_current_state()
            assert current.state == state
            assert current.metadata["message"] == message
    
    async def test_error_state(self, state_tracker):
        """測試錯誤狀態"""
        error_info = {
            "error_type": "validation_error",
            "message": "Invalid input"
        }
        
        await state_tracker.set_state(DialogueState.ERROR, error_info)
        current = await state_tracker.get_current_state()
        
        assert current.state == DialogueState.ERROR
        assert current.metadata["error_type"] == "validation_error"
        assert current.metadata["message"] == "Invalid input"
    
    async def test_state_data_immutability(self, state_tracker):
        """測試狀態數據的不可變性"""
        metadata = {"counter": 0}
        await state_tracker.set_state(DialogueState.ACTIVE, metadata)
        
        # 修改原始元數據
        metadata["counter"] = 1
        
        # 獲取當前狀態
        current = await state_tracker.get_current_state()
        assert current.metadata["counter"] == 0  # 應該保持原值 