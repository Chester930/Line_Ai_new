from typing import Dict, Optional
from datetime import datetime
from .base import BaseSession, Message
from .memory import MemorySession
from ..utils.logger import logger
from ..utils.helpers import generate_session_id

class SessionManager:
    """會話管理器"""
    
    def __init__(
        self,
        session_timeout: int = 3600,  # 1小時
        max_sessions: int = 1000,
        max_messages: int = 50
    ):
        self.session_timeout = session_timeout
        self.max_sessions = max_sessions
        self.max_messages = max_messages
        self.sessions: Dict[str, BaseSession] = {}
    
    async def get_session(
        self,
        session_id: str,
        user_id: Optional[str] = None
    ) -> Optional[BaseSession]:
        """獲取會話"""
        try:
            session = self.sessions.get(session_id)
            
            # 檢查會話是否存在且未過期
            if session and not session.is_expired(self.session_timeout):
                if user_id and session.user_id != user_id:
                    return None
                return session
                
            # 如果會話過期或不存在，且提供了用戶ID，創建新會話
            if user_id:
                return await self.create_session(user_id)
                
            return None
            
        except Exception as e:
            logger.error(f"獲取會話失敗: {str(e)}")
            return None
    
    async def create_session(
        self,
        user_id: str,
        session_id: Optional[str] = None
    ) -> BaseSession:
        """創建會話"""
        try:
            # 生成會話ID
            session_id = session_id or generate_session_id(user_id)
            
            # 檢查會話數量限制
            if len(self.sessions) >= self.max_sessions:
                self._cleanup_expired_sessions()
                
            # 創建新會話
            session = MemorySession(
                session_id=session_id,
                user_id=user_id,
                max_messages=self.max_messages
            )
            
            self.sessions[session_id] = session
            logger.info(f"創建新會話: {session_id} (用戶: {user_id})")
            
            return session
            
        except Exception as e:
            logger.error(f"創建會話失敗: {str(e)}")
            return None
    
    async def add_message(
        self,
        session_id: str,
        content: str,
        role: str = "user"
    ) -> bool:
        """添加消息"""
        try:
            session = await self.get_session(session_id)
            if not session:
                return False
                
            message = Message(role=role, content=content)
            return await session.add_message(message)
            
        except Exception as e:
            logger.error(f"添加消息失敗: {str(e)}")
            return False
    
    def _cleanup_expired_sessions(self):
        """清理過期會話"""
        expired = [
            sid for sid, session in self.sessions.items()
            if session.is_expired(self.session_timeout)
        ]
        
        for session_id in expired:
            del self.sessions[session_id]
            
        if expired:
            logger.info(f"清理 {len(expired)} 個過期會話")
    
    async def close_session(self, session_id: str) -> bool:
        """關閉會話"""
        try:
            if session_id in self.sessions:
                del self.sessions[session_id]
                logger.info(f"關閉會話: {session_id}")
                return True
            return False
            
        except Exception as e:
            logger.error(f"關閉會話失敗: {str(e)}")
            return False 