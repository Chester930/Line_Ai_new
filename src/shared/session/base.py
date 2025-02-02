from abc import ABC, abstractmethod
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from uuid import UUID, uuid4
from dataclasses import dataclass, field

@dataclass
class Message:
    """對話消息"""
    id: UUID
    role: str
    content: str
    user_id: str
    type: str = "text"
    timestamp: datetime = field(default_factory=datetime.now)
    metadata: Dict[str, Any] = field(default_factory=dict)

    @classmethod
    def create(
        cls,
        user_id: str,
        content: str,
        role: str = "user",
        message_type: str = "text",
        metadata: Optional[Dict] = None
    ) -> "Message":
        """創建消息實例"""
        return cls(
            id=uuid4(),
            user_id=user_id,
            role=role,
            content=content,
            type=message_type,
            metadata=metadata or {}
        )

@dataclass
class AIResponse:
    """AI 回應類"""
    text: str
    model: str
    tokens: int
    raw_response: Optional[Dict[str, Any]] = None
    
    @classmethod
    def create(
        cls,
        text: str,
        model: str,
        tokens: int,
        raw_response: Optional[Dict[str, Any]] = None
    ) -> "AIResponse":
        return cls(
            text=text,
            model=model,
            tokens=tokens,
            raw_response=raw_response
        )
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "text": self.text,
            "model": self.model,
            "tokens": self.tokens,
            "raw_response": self.raw_response
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "AIResponse":
        return cls(
            text=data["text"],
            model=data["model"],
            tokens=data["tokens"],
            raw_response=data.get("raw_response")
        )

class Session:
    """會話類"""
    def __init__(self, session_id: str, user_id: str, **kwargs):
        self.id = session_id
        self.user_id = user_id
        self.created_at = datetime.now()
        self.last_activity = datetime.now()
        self.data: Dict = kwargs.get('data', {})
        self.messages: List[Message] = []
        self.ttl = int(kwargs.get('ttl', 3600))  # 確保 ttl 是整數

    def is_expired(self) -> bool:
        """檢查會話是否過期"""
        if isinstance(self.last_activity, int):
            # 如果是整數，假設是時間戳
            last_activity = datetime.fromtimestamp(self.last_activity)
        else:
            last_activity = self.last_activity
        
        now = datetime.now()
        return (now - last_activity).total_seconds() > self.ttl

    async def add_message(self, message: Message) -> bool:
        """添加消息到會話"""
        try:
            self.messages.append(message)
            self.last_activity = datetime.now()
            return True
        except Exception:
            return False

    def get_messages(
        self,
        limit: Optional[int] = None,
        message_type: Optional[str] = None,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None
    ) -> List[Message]:
        """獲取消息歷史
        
        Args:
            limit: 限制返回的消息數量
            message_type: 消息類型過濾
            start_time: 開始時間（包含）
            end_time: 結束時間（包含）
        """
        filtered_messages = self.messages.copy()

        if message_type:
            filtered_messages = [m for m in filtered_messages if m.type == message_type]

        if start_time:
            filtered_messages = [m for m in filtered_messages if m.timestamp >= start_time]

        if end_time:
            filtered_messages = [m for m in filtered_messages if m.timestamp <= end_time]

        # 按時間戳升序排序（從舊到新）
        filtered_messages.sort(key=lambda x: x.timestamp, reverse=False)

        if limit:
            filtered_messages = filtered_messages[-limit:]

        return filtered_messages

    def clear_messages(self):
        """清空消息歷史"""
        self.messages = []

    def update_metadata(self, metadata: Dict[str, Any]):
        """更新元數據"""
        self.data.update(metadata)

    def remove_metadata(self, key: str):
        """移除指定的元數據"""
        self.data.pop(key, None)

    def to_dict(self) -> Dict:
        """將會話轉換為字典格式"""
        return {
            "id": self.id,
            "user_id": self.user_id,
            "created_at": self.created_at.isoformat(),
            "last_activity": self.last_activity.isoformat(),
            "ttl": self.ttl,
            "data": self.data,
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

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Session":
        """從字典創建會話"""
        session = cls(data["id"], data["user_id"])
        session.messages = [Message(**msg) for msg in data["messages"]]
        session.created_at = datetime.fromisoformat(data["created_at"])
        session.last_activity = datetime.fromisoformat(data["last_activity"])
        session.data = data["data"]
        return session

    def update_activity(self):
        """更新最後活動時間"""
        self.last_activity = datetime.now()

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