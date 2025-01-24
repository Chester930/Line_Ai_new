from typing import Dict, List, Type
from .base import BaseEvent, EventHandler
from ..utils.logger import logger

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
    
    async def publish(self, event: BaseEvent):
        """發布事件"""
        handlers = self._handlers.get(event.event_type, [])
        
        if not handlers:
            logger.warning(f"沒有處理器訂閱事件: {event.event_type}")
            return
        
        logger.debug(
            f"發布事件 {event.event_type} "
            f"(ID: {event.event_id})"
        )
        
        for handler in handlers:
            try:
                await handler.handle(event)
            except Exception as e:
                logger.error(
                    f"事件處理失敗 {event.event_type} "
                    f"(Handler: {handler.__class__.__name__}): "
                    f"{str(e)}"
                )

# 創建全局事件發布器實例
event_publisher = EventPublisher() 