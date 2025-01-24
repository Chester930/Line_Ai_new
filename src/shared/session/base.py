from abc import ABC, abstractmethod
from typing import Dict, List, Optional, Any
from datetime import datetime
from dataclasses import dataclass, field
from uuid import uuid4

@dataclass
class Message:
    """會話消息"""
    role: str
    content: str
    message_id: str = field(default_factory=lambda: str(uuid4()))
    timestamp: datetime = field(default_factory=datetime.now)
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = datetime.now()
    
    def to_dict(self) -> Dict:
        """轉換為字典"""
        return {
            "role": self.role,
            "content": self.content,
            "timestamp": self.timestamp.isoformat()
        }

@dataclass
class Session:
    """會話"""
    session_id: str = field(default_factory=lambda: str(uuid4()))
    user_id: str = ""
    messages: List[Message] = field(default_factory=list)
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def add_message(self, message: Message):
        """添加消息"""
        self.messages.append(message)
        self.updated_at = datetime.now()
    
    def clear_messages(self):
        """清空消息"""
        self.messages.clear()
        self.updated_at = datetime.now()
    
    def get_messages(
        self,
        limit: Optional[int] = None,
        before: Optional[datetime] = None
    ) -> List[Message]:
        """獲取消息"""
        messages = self.messages
        
        if before:
            messages = [
                msg for msg in messages
                if msg.timestamp < before
            ]
        
        if limit:
            messages = messages[-limit:]
        
        return messages

class BaseSessionManager(ABC):
    """會話管理器基類"""
    
    @abstractmethod
    async def get_session(
        self,
        session_id: str
    ) -> Optional[Session]:
        """獲取會話"""
        pass
    
    @abstractmethod
    async def create_session(
        self,
        user_id: str,
        metadata: Optional[Dict[str, Any]] = None
    ) -> Session:
        """創建會話"""
        pass
    
    @abstractmethod
    async def save_session(
        self,
        session: Session
    ) -> bool:
        """保存會話"""
        pass
    
    @abstractmethod
    async def delete_session(
        self,
        session_id: str
    ) -> bool:
        """刪除會話"""
        pass
    
    @abstractmethod
    async def list_sessions(
        self,
        user_id: Optional[str] = None
    ) -> List[Session]:
        """列出會話"""
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