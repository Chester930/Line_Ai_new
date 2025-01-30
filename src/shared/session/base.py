from abc import ABC, abstractmethod
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from uuid import UUID, uuid4
from dataclasses import dataclass

@dataclass
class Message:
    """消息類"""
    id: UUID
    user_id: str
    content: str
    timestamp: datetime
    type: str = "text"
    metadata: Dict[str, Any] = None

    def __init__(
        self,
        user_id: str,
        content: str,
        message_type: str = "text",
        metadata: Optional[Dict] = None
    ):
        self.id = uuid4()
        self.user_id = user_id
        self.content = content
        self.type = message_type
        self.timestamp = datetime.utcnow()
        self.metadata = metadata or {}

class Session:
    """會話類"""
    def __init__(
        self,
        session_id: str,
        user_id: str,
        ttl: int = 3600,
        metadata: Optional[Dict] = None
    ):
        self.id = session_id
        self.user_id = user_id
        self.ttl = ttl
        self.created_at = datetime.utcnow()
        self.last_activity = datetime.utcnow()
        self.messages: List[Message] = []
        self.metadata = metadata or {}

    def is_expired(self) -> bool:
        """檢查會話是否過期"""
        return (datetime.utcnow() - self.last_activity).total_seconds() > self.ttl

    def update_activity(self):
        """更新最後活動時間"""
        self.last_activity = datetime.utcnow()

    def add_message(self, message: Message):
        """添加消息到會話"""
        self.messages.append(message)
        self.update_activity()

    def get_messages(
        self,
        limit: Optional[int] = None,
        message_type: Optional[str] = None,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None
    ) -> List[Message]:
        """獲取消息歷史"""
        filtered_messages = self.messages

        if message_type:
            filtered_messages = [m for m in filtered_messages if m.type == message_type]

        if start_time:
            filtered_messages = [m for m in filtered_messages if m.timestamp >= start_time]

        if end_time:
            filtered_messages = [m for m in filtered_messages if m.timestamp <= end_time]

        if limit:
            filtered_messages = filtered_messages[-limit:]

        return filtered_messages

    def clear_messages(self):
        """清空消息歷史"""
        self.messages = []

    def update_metadata(self, metadata: Dict[str, Any]):
        """更新元數據"""
        self.metadata.update(metadata)

    def remove_metadata(self, key: str):
        """移除指定的元數據"""
        self.metadata.pop(key, None)

    def to_dict(self) -> Dict:
        """將會話轉換為字典格式"""
        return {
            "id": self.id,
            "user_id": self.user_id,
            "created_at": self.created_at.isoformat(),
            "last_activity": self.last_activity.isoformat(),
            "ttl": self.ttl,
            "metadata": self.metadata,
            "messages": [
                {
                    "id": str(msg.id),
                    "user_id": msg.user_id,
                    "content": msg.content,
                    "type": msg.type,
                    "timestamp": msg.timestamp.isoformat(),
                    "metadata": msg.metadata
                }
                for msg in self.messages
            ]
        }

class BaseSessionManager(ABC):
    """會話管理器基類"""
    
    @abstractmethod
    async def create_session(
        self,
        user_id: str,
        ttl: int = 3600,
        metadata: Dict[str, Any] = None
    ) -> Session:
        """創建新會話"""
        pass

    @abstractmethod
    async def get_session(
        self,
        session_id: str
    ) -> Optional[Session]:
        """獲取會話"""
        pass

    @abstractmethod
    async def update_session(
        self,
        session: Session
    ) -> bool:
        """更新會話"""
        pass

    @abstractmethod
    async def delete_session(
        self,
        session_id: str
    ) -> bool:
        """刪除會話"""
        pass

    @abstractmethod
    async def cleanup_expired(self) -> int:
        """清理過期會話"""
        pass

class BaseSession(ABC):
    """會話基類"""
    
    def __init__(
        self,
        session_id: str,
        user_id: str,
        max_messages: int = 50
    ):
        self.session_id = session_id
        self.user_id = user_id
        self.max_messages = max_messages
        self.messages: List[Message] = []
        self.metadata: Dict[str, Any] = {}
        self.created_at = datetime.now()
        self.last_active = datetime.now()
    
    @abstractmethod
    async def add_message(self, message: Message) -> bool:
        """添加消息"""
        pass
    
    @abstractmethod
    async def get_messages(
        self,
        limit: Optional[int] = None
    ) -> List[Message]:
        """獲取消息"""
        pass
    
    @abstractmethod
    async def clear_messages(self) -> bool:
        """清空消息"""
        pass
    
    @abstractmethod
    async def set_metadata(self, key: str, value: Any) -> bool:
        """設置元數據"""
        pass
    
    @abstractmethod
    async def get_metadata(self, key: str) -> Optional[Any]:
        """獲取元數據"""
        pass
    
    def is_expired(self, timeout: int) -> bool:
        """檢查會話是否過期"""
        if not timeout:
            return False
        
        delta = datetime.now() - self.last_active
        return delta.total_seconds() > timeout
    
    def update_activity(self):
        """更新活動時間"""
        self.last_active = datetime.now() 