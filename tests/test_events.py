import pytest
from src.shared.events.base import EventEmitter
from src.shared.events.types import Event
from typing import List, Dict, Any
import asyncio

class TestEventEmitter:
    @pytest.fixture
    def event_emitter(self):
        return EventEmitter()
    
    @pytest.mark.asyncio
    async def test_emit_and_listen(self, event_emitter):
        received_events: List[Event] = []
        
        async def handler(event: Event):
            received_events.append(event)
        
        # 註冊事件處理器
        event_emitter.on("test_event", handler)
        
        # 發送事件
        test_event = Event(
            type="test_event",
            data={"message": "Hello"}
        )
        await event_emitter.emit(test_event)
        
        # 等待異步處理完成
        await asyncio.sleep(0.1)
        
        assert len(received_events) == 1
        assert received_events[0].type == "test_event"
        assert received_events[0].data["message"] == "Hello"
        
    @pytest.mark.asyncio
    async def test_multiple_handlers(self, event_emitter):
        received_events_1: List[Event] = []
        received_events_2: List[Event] = []
        
        async def handler1(event: Event):
            received_events_1.append(event)
            
        async def handler2(event: Event):
            received_events_2.append(event)
        
        # 註冊多個處理器
        event_emitter.on("test_event", handler1)
        event_emitter.on("test_event", handler2)
        
        # 發送事件
        test_event = Event(
            type="test_event",
            data={"message": "Hello"}
        )
        await event_emitter.emit(test_event)
        
        await asyncio.sleep(0.1)
        
        assert len(received_events_1) == 1
        assert len(received_events_2) == 1 

    @pytest.mark.asyncio
    async def test_remove_handler(self, event_emitter):
        """測試移除事件處理器"""
        received_events: List[Event] = []
        
        async def handler(event: Event):
            received_events.append(event)
            
        # 註冊然後移除處理器
        event_emitter.on("test_event", handler)
        event_emitter.remove_handler("test_event", handler)
        
        # 發送事件
        test_event = Event(
            type="test_event",
            data={"message": "Hello"}
        )
        await event_emitter.emit(test_event)
        
        await asyncio.sleep(0.1)
        assert len(received_events) == 0
        
    @pytest.mark.asyncio
    async def test_wildcard_events(self, event_emitter):
        """測試通配符事件監聽"""
        events: Dict[str, List[Dict[str, Any]]] = {
            "user": [],
            "message": []
        }
        
        async def user_handler(event: Event):
            events["user"].append(event.data)
            
        async def message_handler(event: Event):
            events["message"].append(event.data)
            
        # 註冊通配符處理器
        event_emitter.on("user.*", user_handler)
        event_emitter.on("message.*", message_handler)
        
        # 發送不同類型的事件
        await event_emitter.emit(Event("user.created", {"id": 1}))
        await event_emitter.emit(Event("user.updated", {"id": 1, "name": "test"}))
        await event_emitter.emit(Event("message.sent", {"text": "hello"}))
        
        await asyncio.sleep(0.1)
        
        assert len(events["user"]) == 2
        assert len(events["message"]) == 1
        
    @pytest.mark.asyncio
    async def test_error_handling(self, event_emitter):
        """測試錯誤處理"""
        error_caught = False
        
        async def error_handler(event: Event):
            raise Exception("Test error")
            
        async def error_callback(error: Exception, event: Event):
            nonlocal error_caught
            error_caught = True
            assert isinstance(error, Exception)
            assert error.args[0] == "Test error"
            
        # 註冊錯誤處理器
        event_emitter.on("test_event", error_handler)
        event_emitter.on_error(error_callback)
        
        # 發送事件
        await event_emitter.emit(Event("test_event", {}))
        
        await asyncio.sleep(0.1)
        assert error_caught
        
    @pytest.mark.asyncio
    async def test_once_handler(self, event_emitter):
        """測試一次性事件處理器"""
        received_events: List[Event] = []
        
        async def handler(event: Event):
            received_events.append(event)
            
        # 註冊一次性處理器
        event_emitter.once("test_event", handler)
        
        # 發送兩次事件
        test_event = Event("test_event", {"count": 1})
        await event_emitter.emit(test_event)
        await event_emitter.emit(test_event)
        
        await asyncio.sleep(0.1)
        assert len(received_events) == 1
        
    @pytest.mark.asyncio
    async def test_event_priority(self, event_emitter):
        """測試事件處理優先級"""
        execution_order: List[int] = []
        
        async def handler1(event: Event):
            execution_order.append(1)
            
        async def handler2(event: Event):
            execution_order.append(2)
            
        async def handler3(event: Event):
            execution_order.append(3)
            
        # 按不同優先級註冊處理器
        event_emitter.on("test_event", handler2, priority=2)
        event_emitter.on("test_event", handler1, priority=1)
        event_emitter.on("test_event", handler3, priority=3)
        
        # 發送事件
        await event_emitter.emit(Event("test_event", {}))
        
        await asyncio.sleep(0.1)
        assert execution_order == [1, 2, 3] 