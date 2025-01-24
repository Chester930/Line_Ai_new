import pytest
from datetime import datetime
from src.shared.events.base import BaseEvent, EventHandler
from src.shared.events.publisher import EventPublisher
from src.shared.events.types import (
    MessageEvent,
    UserEvent,
    SystemEvent,
    ErrorEvent
)

class TestEventHandler(EventHandler):
    """測試事件處理器"""
    def __init__(self):
        self.handled_events = []
    
    async def _handle_event(self, event: BaseEvent) -> bool:
        self.handled_events.append(event)
        return True

@pytest.fixture
def event_publisher():
    """事件發布器"""
    return EventPublisher()

@pytest.fixture
def event_handler():
    """事件處理器"""
    return TestEventHandler()

@pytest.mark.asyncio
async def test_event_publishing(event_publisher, event_handler):
    """測試事件發布"""
    # 訂閱事件
    event_publisher.subscribe("message", event_handler)
    
    # 創建並發布事件
    event = MessageEvent(
        message_id="test_id",
        user_id="test_user",
        content="Hello"
    )
    await event_publisher.publish(event)
    
    # 驗證事件處理
    assert len(event_handler.handled_events) == 1
    handled_event = event_handler.handled_events[0]
    assert handled_event.event_type == "message"
    assert handled_event.data["content"] == "Hello"

@pytest.mark.asyncio
async def test_multiple_handlers(event_publisher):
    """測試多個處理器"""
    handler1 = TestEventHandler()
    handler2 = TestEventHandler()
    
    # 訂閱相同事件
    event_publisher.subscribe("user", handler1)
    event_publisher.subscribe("user", handler2)
    
    # 發布事件
    event = UserEvent(
        user_id="test_user",
        action="login"
    )
    await event_publisher.publish(event)
    
    # 驗證兩個處理器都收到事件
    assert len(handler1.handled_events) == 1
    assert len(handler2.handled_events) == 1

def test_event_data_conversion():
    """測試事件數據轉換"""
    # 系統事件
    system_event = SystemEvent(
        action="startup",
        details={"version": "1.0"}
    )
    data = system_event.to_dict()
    assert data["event_type"] == "system"
    assert data["data"]["action"] == "startup"
    
    # 錯誤事件
    error_event = ErrorEvent(
        error_type="validation",
        message="Invalid input",
        details={"field": "email"}
    )
    data = error_event.to_dict()
    assert data["event_type"] == "error"
    assert data["data"]["error_type"] == "validation"

@pytest.mark.asyncio
async def test_event_unsubscribe(event_publisher, event_handler):
    """測試取消訂閱"""
    # 訂閱事件
    event_publisher.subscribe("test", event_handler)
    
    # 發布第一個事件
    event1 = BaseEvent(event_type="test")
    await event_publisher.publish(event1)
    assert len(event_handler.handled_events) == 1
    
    # 取消訂閱
    event_publisher.unsubscribe("test", event_handler)
    
    # 發布第二個事件
    event2 = BaseEvent(event_type="test")
    await event_publisher.publish(event2)
    assert len(event_handler.handled_events) == 1  # 仍然是1 