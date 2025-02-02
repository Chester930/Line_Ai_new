import pytest
from unittest.mock import AsyncMock
from src.shared.events.system import EventSystem

@pytest.mark.asyncio
class TestEventSystem:
    @pytest.fixture
    async def event_system(self):
        return EventSystem()
    
    async def test_track_event(self, event_system):
        """測試事件追蹤"""
        # 追蹤事件
        await event_system.track(
            "test_event",
            {"key": "value"}
        )
        
        # 驗證事件發布
        assert len(event_system.publisher._handlers) == 0  # 因為沒有訂閱者
    
    async def test_track_error(self, event_system):
        """測試錯誤處理"""
        # 模擬發布錯誤
        event_system.publisher.publish = AsyncMock(
            side_effect=Exception("Publish error")
        )
        
        # 應該不會拋出異常
        await event_system.track(
            "test_event",
            {"key": "value"}
        ) 