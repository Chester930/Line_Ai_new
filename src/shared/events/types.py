from dataclasses import dataclass
from datetime import datetime
from typing import Any, Dict, Optional
from .base import BaseEvent

@dataclass
class MessageEvent(BaseEvent):
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
            event_type="message",
            data={
                "message_id": message_id,
                "user_id": user_id,
                "content": content,
                "message_type": message_type,
                **kwargs
            }
        )

@dataclass
class UserEvent(BaseEvent):
    """用戶事件"""
    def __init__(
        self,
        user_id: str,
        action: str,
        **kwargs
    ):
        super().__init__(
            event_type="user",
            data={
                "user_id": user_id,
                "action": action,
                **kwargs
            }
        )

@dataclass
class SystemEvent(BaseEvent):
    """系統事件"""
    def __init__(
        self,
        action: str,
        details: Optional[Dict[str, Any]] = None,
        **kwargs
    ):
        super().__init__(
            event_type="system",
            data={
                "action": action,
                "details": details or {},
                **kwargs
            }
        )

@dataclass
class ErrorEvent(BaseEvent):
    """錯誤事件"""
    def __init__(
        self,
        error_type: str,
        message: str,
        details: Optional[Dict[str, Any]] = None,
        **kwargs
    ):
        super().__init__(
            event_type="error",
            data={
                "error_type": error_type,
                "message": message,
                "details": details or {},
                **kwargs
            }
        ) 