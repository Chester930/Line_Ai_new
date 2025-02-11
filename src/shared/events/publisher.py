from typing import Dict, List, Type, Any
from .base import BaseEvent, EventHandler
from ..utils.logger import logger
from ..exceptions import EventError

class EventPublisher:
    """事件發布器"""
    
    def __init__(self):
        self._handlers: Dict[str, List[EventHandler]] = {}
    
    def subscribe(
        self,
        event_type: str,
        handler: EventHandler
    ):
        """訂閱事件"""
        if event_type not in self._handlers:
            self._handlers[event_type] = []
        self._handlers[event_type].append(handler)
        logger.debug(
            f"已訂閱事件 {event_type}: "
            f"{handler.__class__.__name__}"
        )
    
    def unsubscribe(
        self,
        event_type: str,
        handler: EventHandler
    ):
        """取消訂閱"""
        if event_type in self._handlers:
            self._handlers[event_type] = [
                h for h in self._handlers[event_type]
                if h is not handler
            ]
            logger.debug(
                f"已取消訂閱事件 {event_type}: "
                f"{handler.__class__.__name__}"
            )
    
    async def publish(self, event_type: str, event: BaseEvent) -> None:
        """發布事件"""
        if event_type not in self._handlers:
            raise EventError(f"沒有訂閱者處理事件類型: {event_type}")
        
        for handler in self._handlers[event_type]:
            try:
                await handler(event)
            except Exception as e:
                logger.error(f"處理事件失敗: {str(e)}")
                raise EventError(f"處理事件失敗: {str(e)}")

# 創建全局事件發布器實例
event_publisher = EventPublisher() 