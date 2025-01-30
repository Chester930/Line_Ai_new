from typing import Dict, List, Optional, Any
from datetime import datetime
from .base import BaseSession, Message, Session, BaseSessionManager
from ..utils.logger import logger
from uuid import uuid4

class MemorySession(Session):
    """記憶體會話管理器"""
    
    def __init__(self, session_id: str, user_id: str, metadata: Dict[str, Any] = None):
        super().__init__(session_id=session_id, user_id=user_id)  # 確保 session_id 被正確傳遞
        self.metadata = metadata or {}
        self.messages = []  # 確保 messages 屬性被初始化
    
    async def add_message(self, message: Message) -> bool:
        """添加消息"""
        try:
            self.update_activity()
            self.messages.append(message)
            while len(self.messages) > self.max_messages:
                self.messages.pop(0)
            return True
        except Exception:
            return False
    
    async def get_messages(self, limit: Optional[int] = None) -> List[Message]:
        """獲取消息"""
        self.update_activity()
        if limit is None:
            return self.messages.copy()
        return self.messages[-limit:]
    
    async def clear_messages(self) -> bool:
        """清空消息"""
        try:
            self.update_activity()
            self.messages.clear()
            return True
        except Exception:
            return False
    
    async def set_metadata(self, key: str, value: Any) -> bool:
        """設置元數據"""
        try:
            self.update_activity()
            self.metadata[key] = value
            return True
        except Exception:
            return False
    
    async def get_metadata(self, key: str) -> Optional[Any]:
        """獲取元數據"""
        self.update_activity()
        return self.metadata.get(key)

class MemorySessionManager(BaseSessionManager):
    """記憶體會話管理器"""
    
    def __init__(self):
        self.sessions: Dict[str, Session] = {}
    
    async def create_session(
        self,
        user_id: str,
        metadata: Optional[Dict] = None,
        ttl: int = 3600
    ) -> Session:
        """創建新會話"""
        session_id = str(uuid4())
        session = Session(
            session_id=session_id,
            user_id=user_id,
            ttl=ttl,
            metadata=metadata
        )
        self.sessions[session_id] = session
        logger.info(f"創建新會話: {session_id}")
        return session
    
    async def get_session(self, session_id: str) -> Optional[Session]:
        """獲取會話"""
        session = self.sessions.get(session_id)
        if session and not session.is_expired():
            return session
        elif session:
            await self.delete_session(session_id)
        return None
    
    async def update_session(self, session: Session) -> bool:
        """更新會話"""
        if session.id in self.sessions:
            self.sessions[session.id] = session
            logger.debug(f"更新會話: {session.id}")
            return True
        return False
    
    async def save_session(self, session: Session) -> bool:
        """保存會話"""
        if session.id in self.sessions:
            self.sessions[session.id] = session
            return True
        return False
    
    async def delete_session(self, session_id: str) -> bool:
        """刪除會話"""
        if session_id in self.sessions:
            del self.sessions[session_id]
            logger.info(f"刪除會話: {session_id}")
            return True
        return False
    
    async def cleanup_expired(self) -> int:
        """清理過期會話"""
        expired_count = 0
        expired_sessions = [
            session_id for session_id, session in self.sessions.items()
            if session.is_expired()
        ]
        
        for session_id in expired_sessions:
            if await self.delete_session(session_id):
                expired_count += 1
        
        if expired_count > 0:
            logger.info(f"清理了 {expired_count} 個過期會話")
        return expired_count
    
    async def list_sessions(self, user_id: Optional[str] = None) -> List[Session]:
        """列出會話"""
        # 清理過期會話
        await self.cleanup_expired()
        
        # 過濾會話
        if user_id:
            return [
                session for session in self.sessions.values()
                if session.user_id == user_id
            ]
        return list(self.sessions.values())