import logging
from typing import Dict, Any
from .publisher import EventPublisher
from .base import BaseEvent

logger = logging.getLogger(__name__)

class EventSystem:
    """事件系統"""
    
    def __init__(self):
        self.publisher = EventPublisher()
        
    async def track(self, event_type: str, data: Dict[str, Any]) -> None:
        """追蹤事件"""
        try:
            event = BaseEvent(
                event_type=event_type,
                data=data
            )
            await self.publisher.publish(event)
            
        except Exception as e:
            logger.error(f"事件追蹤失敗: {str(e)}") 