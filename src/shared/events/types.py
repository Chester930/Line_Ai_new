from dataclasses import dataclass, field
from datetime import datetime
from typing import Dict, Any, Optional
from uuid import uuid4

@dataclass
class Event:
    """基礎事件類型"""
    type: str
    data: Dict[str, Any]
    timestamp: Optional[datetime] = None
    event_id: str = field(default_factory=lambda: str(uuid4()))
    source: str = "system"
    
    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = datetime.now()
            
    def to_dict(self) -> Dict[str, Any]:
        """轉換為字典"""
        return {
            "event_id": self.event_id,
            "type": self.type,
            "timestamp": self.timestamp.isoformat(),
            "source": self.source,
            "data": self.data
        }

# 特定事件類型
@dataclass
class MessageEvent(Event):
    """消息事件"""
    def __init__(
        self,
        message_id: str,
        user_id: str,
        content: str,
        message_type: str = "text",
        **kwargs
    ):
        super().__init__(
            type="message",
            data={
                "message_id": message_id,
                "user_id": user_id,
                "content": content,
                "message_type": message_type,
                **kwargs
            }
        )

@dataclass
class UserEvent(Event):
    """用戶事件"""
    def __init__(
        self,
        user_id: str,
        action: str,
        **kwargs
    ):
        super().__init__(
            type="user",
            data={
                "user_id": user_id,
                "action": action,
                **kwargs
            }
        )

@dataclass
class SystemEvent(Event):
    """系統事件"""
    def __init__(
        self,
        action: str,
        details: Optional[Dict[str, Any]] = None,
        **kwargs
    ):
        super().__init__(
            type="system",
            data={
                "action": action,
                "details": details or {},
                **kwargs
            }
        )

@dataclass
class ErrorEvent(Event):
    """錯誤事件"""
    def __init__(
        self,
        error_type: str,
        message: str,
        details: Optional[Dict[str, Any]] = None,
        **kwargs
    ):
        super().__init__(
            type="error",
            data={
                "error_type": error_type,
                "message": message,
                "details": details or {},
                **kwargs
            }
        ) 