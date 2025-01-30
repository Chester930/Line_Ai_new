# src/shared/session/memory.py

from typing import Dict, Optional
from .base import Session

class MemorySessionManager:
    def __init__(self):
        self.sessions: Dict[str, Session] = {}

    async def create_session(self, user_id: str, metadata: dict) -> Session:
        session = Session(user_id=user_id, metadata=metadata)
        self.sessions[session.session_id] = session
        return session

    async def save_session(self, session: Session) -> bool:
        self.sessions[session.session_id] = session
        return True

    async def get_session(self, session_id: str) -> Optional[Session]:
        return self.sessions.get(session_id)

    async def list_sessions(self, user_id: Optional[str] = None):
        if user_id:
            return [s for s in self.sessions.values() if s.user_id == user_id]
        return list(self.sessions.values())

    async def delete_session(self, session_id: str) -> bool:
        if session_id in self.sessions:
            del self.sessions[session_id]
            return True
        return False

class MemorySession(Session):
    """記憶體會話管理器"""
    
    def __init__(self, session_id: str, user_id: str, max_messages: int = 50, metadata: Dict[str, Any] = None):
        super().__init__(session_id=session_id, user_id=user_id, max_messages=max_messages)
        self.metadata = metadata or {}