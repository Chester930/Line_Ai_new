from abc import ABC
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Dict, Optional
from uuid import uuid4

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
    
    async def handle(self, event: BaseEvent) -> bool:
        """處理事件"""
        try:
            return await self._handle_event(event)
        except Exception as e:
            self._handle_error(event, e)
            return False
    
    async def _handle_event(self, event: BaseEvent) -> bool:
        """實際處理事件的邏輯"""
        return True
    
    def _handle_error(self, event: BaseEvent, error: Exception):
        """處理錯誤"""
        from ..utils.logger import logger
        logger.error(
            f"處理事件失敗: {event.event_type} "
            f"(ID: {event.event_id}): {str(error)}"
        ) 