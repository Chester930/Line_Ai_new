import pytest
from datetime import datetime
from src.shared.cag.state import StateTracker, DialogueState, StateData

@pytest.mark.asyncio
class TestStateTracker:
    async def test_initial_state(self):
        tracker = StateTracker()
        assert tracker.current_state is None
        assert len(tracker.state_history) == 0
    
    async def test_set_state(self):
        tracker = StateTracker()
        
        # 設置初始狀態
        await tracker.set_state(DialogueState.INIT)
        
        assert tracker.current_state is not None
        assert tracker.current_state.state == DialogueState.INIT
        assert isinstance(tracker.current_state.updated_at, datetime)
        
        # 設置新狀態
        await tracker.set_state(DialogueState.ACTIVE)
        
        # 驗證狀態更新和歷史記錄
        assert tracker.current_state.state == DialogueState.ACTIVE
        assert len(tracker.state_history) == 1
        assert tracker.state_history[0].state == DialogueState.INIT
    
    async def test_state_with_metadata(self):
        tracker = StateTracker()
        metadata = {"user_id": "123", "session": "abc"}
        
        await tracker.set_state(DialogueState.ACTIVE, metadata)
        
        assert tracker.current_state.metadata == metadata 