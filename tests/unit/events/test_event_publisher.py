import pytest
from src.shared.events.publisher import EventPublisher
from src.shared.events.base import Event, BaseEvent
from src.shared.exceptions import EventError
from datetime import datetime

class TestEventPublisher:
    @pytest.fixture
    def publisher(self):
        return EventPublisher()
    
    @pytest.mark.asyncio
    async def test_basic_publish_subscribe(self, publisher):
        """測試基本的發布訂閱功能"""
        events = []
        
        async def handler(event: BaseEvent):
            events.append(event)
        
        event = BaseEvent(
            event_type="test",
            data={"message": "test"},
            timestamp=datetime.now()
        )
        
        publisher.subscribe("test", handler)
        await publisher.publish("test", event)
        
        assert len(events) == 1
        assert events[0].data["message"] == "test"
    
    @pytest.mark.asyncio
    async def test_multiple_subscribers(self, publisher):
        """測試多個訂閱者"""
        events1, events2 = [], []
        
        async def handler1(event: BaseEvent):
            events1.append(event)
            
        async def handler2(event: BaseEvent):
            events2.append(event)
        
        publisher.subscribe("test", handler1)
        publisher.subscribe("test", handler2)
        
        event = BaseEvent(
            event_type="test",
            data={"message": "test"}
        )
        await publisher.publish("test", event)
        
        assert len(events1) == len(events2) == 1
        assert events1[0].data["message"] == events2[0].data["message"] == "test"
    
    @pytest.mark.asyncio
    async def test_unsubscribe(self, publisher):
        """測試取消訂閱"""
        events = []
        
        async def handler(event):
            events.append(event)
        
        publisher.subscribe("test", handler)
        event = BaseEvent(event_type="test", data={"message": "first"})
        await publisher.publish("test", event)
        
        publisher.unsubscribe("test", handler)
        event = BaseEvent(event_type="test", data={"message": "second"})
        await publisher.publish("test", event)
        
        assert len(events) == 1
        assert events[0].data["message"] == "first"
    
    @pytest.mark.asyncio
    async def test_error_handling(self, publisher):
        """測試錯誤處理"""
        async def error_handler(event):
            raise Exception("Test error")
        
        publisher.subscribe("test", error_handler)
        
        event = BaseEvent(
            event_type="test",
            data={"message": "test"}
        )
        
        with pytest.raises(EventError):
            await publisher.publish("test", event)
    
    @pytest.mark.asyncio
    async def test_event_filtering(self, publisher):
        """測試事件過濾"""
        events = []
        
        async def handler(event: BaseEvent):
            if event.event_type == "important":
                events.append(event)
        
        publisher.subscribe("test", handler)
        
        important_event = BaseEvent(
            event_type="important",
            data={"message": "test1"}
        )
        normal_event = BaseEvent(
            event_type="normal", 
            data={"message": "test2"}
        )
        
        await publisher.publish("test", important_event)
        await publisher.publish("test", normal_event)
        
        assert len(events) == 1
        assert events[0].data["message"] == "test1"

@pytest.mark.asyncio
async def test_event_publisher():
    """整合測試事件發布器"""
    publisher = EventPublisher()
    events = []
    
    # 測試事件訂閱
    async def event_handler(event):
        events.append(event)
    
    publisher.subscribe("test_event", event_handler)
    
    # 測試事件發布
    test_event = BaseEvent(
        event_type="test_event",
        data={"data": "test_data"}
    )
    await publisher.publish("test_event", test_event)
    
    assert len(events) == 1
    assert events[0].data["data"] == "test_data"
    
    # 測試事件取消訂閱
    publisher.unsubscribe("test_event", event_handler)
    invalid_event = BaseEvent(
        event_type="test_event",
        data={"data": "ignored"}
    )
    await publisher.publish("test_event", invalid_event)
    assert len(events) == 1  # 不應該增加
    
    # 測試錯誤處理
    with pytest.raises(EventError):
        await publisher.publish("invalid_event", test_event) 