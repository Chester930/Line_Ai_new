from abc import ABC
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Dict, Optional, Callable, List
from uuid import uuid4
from .types import Event
import asyncio
import re
from ..utils.logger import logger

@dataclass
class BaseEvent:
    """事件基類"""
    event_type: str
    timestamp: datetime = field(default_factory=datetime.now)
    event_id: str = field(default_factory=lambda: str(uuid4()))
    source: str = "system"
    data: Optional[Dict[str, Any]] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """轉換為字典"""
        return {
            "event_id": self.event_id,
            "event_type": self.event_type,
            "timestamp": self.timestamp.isoformat(),
            "source": self.source,
            "data": self.data or {}
        }

class EventHandler(ABC):
    """事件處理器基類"""
    
    async def handle(self, event: BaseEvent) -> Any:
        """處理事件"""
        try:
            return await self._handle_event(event)
        except Exception as e:
            self._handle_error(event, e)
            return None
    
    async def _handle_event(self, event: BaseEvent) -> Any:
        """實際處理事件的邏輯"""
        return None
    
    def _handle_error(self, event: BaseEvent, error: Exception):
        """處理錯誤"""
        logger.error(
            f"處理事件失敗: {event.event_type} "
            f"(ID: {event.event_id}): {str(error)}"
        )

class Event:
    """事件基類"""
    def __init__(self, type: str, data: Dict[str, Any]):
        self.type = type
        self.data = data

EventHandler = Callable[[Event], None]

class EventHandler:
    """事件處理器包裝類"""
    def __init__(self, callback: Callable, priority: int = 0, once: bool = False):
        self.callback = callback
        self.priority = priority
        self.once = once
        
class EventEmitter:
    """事件發射器"""
    def __init__(self):
        self._handlers: Dict[str, List[EventHandler]] = {}
        self._error_handlers: List[Callable] = []
        
    def on(self, event_type: str, handler: Callable, priority: int = 0) -> None:
        """註冊事件處理器"""
        if event_type not in self._handlers:
            self._handlers[event_type] = []
            
        handler_wrapper = EventHandler(handler, priority)
        self._handlers[event_type].append(handler_wrapper)
        # 按優先級排序
        self._handlers[event_type].sort(key=lambda h: h.priority)
        
    def once(self, event_type: str, handler: Callable, priority: int = 0) -> None:
        """註冊一次性事件處理器"""
        if event_type not in self._handlers:
            self._handlers[event_type] = []
            
        handler_wrapper = EventHandler(handler, priority, once=True)
        self._handlers[event_type].append(handler_wrapper)
        self._handlers[event_type].sort(key=lambda h: h.priority)
        
    def remove_handler(self, event_type: str, handler: Callable) -> None:
        """移除事件處理器"""
        if event_type in self._handlers:
            self._handlers[event_type] = [
                h for h in self._handlers[event_type] 
                if h.callback != handler
            ]
            
    def on_error(self, handler: Callable) -> None:
        """註冊錯誤處理器"""
        self._error_handlers.append(handler)
        
    async def emit(self, event: Event) -> None:
        """發送事件"""
        # 查找匹配的處理器
        matched_handlers: List[EventHandler] = []
        
        for pattern, handlers in self._handlers.items():
            # 支持通配符匹配
            if '*' in pattern:
                regex = pattern.replace('.', '\.').replace('*', '.*')
                if re.match(regex, event.type):
                    matched_handlers.extend(handlers)
            elif pattern == event.type:
                matched_handlers.extend(handlers)
                
        # 按優先級排序
        matched_handlers.sort(key=lambda h: h.priority)
        
        # 執行處理器
        for handler in matched_handlers:
            try:
                await handler.callback(event)
                if handler.once:
                    self.remove_handler(event.type, handler.callback)
            except Exception as e:
                logger.error(f"Error handling event {event.type}: {str(e)}")
                # 調用錯誤處理器
                for error_handler in self._error_handlers:
                    try:
                        await error_handler(e, event)
                    except Exception as e2:
                        logger.error(f"Error in error handler: {str(e2)}")
                        
    def clear(self) -> None:
        """清除所有處理器"""
        self._handlers.clear()
        self._error_handlers.clear() 