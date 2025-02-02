from typing import Dict, Optional
from datetime import datetime
import asyncio
from .base import BaseSessionManager, Session, Message
from ..utils.logger import logger
from ..utils.helpers import generate_session_id

class SessionManager(BaseSessionManager):
    """會話管理器實現"""
    
    def __init__(self, config: dict):
        self.config = config
        self.sessions: Dict[str, Session] = {}
        self._cleanup_task = None
    
    async def start(self):
        """啟動會話管理器"""
        self._cleanup_task = asyncio.create_task(self._cleanup_loop())
    
    async def stop(self):
        """停止會話管理器"""
        if self._cleanup_task:
            self._cleanup_task.cancel()
            try:
                await self._cleanup_task
            except asyncio.CancelledError:
                pass
    
    async def create_session(self, user_id: str, **kwargs) -> Session:
        """創建新會話"""
        session_id = generate_session_id()  # 需要實現這個輔助函數
        session = Session(
            session_id=session_id,
            user_id=user_id,
            **kwargs
        )
        self.sessions[session_id] = session
        logger.info(f"Created new session {session.id} for user {user_id}")
        return session
    
    async def get_session(self, session_id: str) -> Optional[Session]:
        """獲取會話"""
        session = self.sessions.get(session_id)
        if session:
            if session.is_expired():
                await self.delete_session(session_id)
                return None
            session.update_activity()  # 更新活動時間
        return session
    
    async def update_session(self, session: Session) -> bool:
        """更新會話"""
        if session.id not in self.sessions:
            return False
        self.sessions[session.id] = session
        return True
    
    async def delete_session(self, session_id: str) -> bool:
        """刪除會話"""
        if session_id in self.sessions:
            del self.sessions[session_id]
            logger.info(f"Deleted session {session_id}")
            return True
        return False
    
    async def cleanup_expired(self) -> int:
        """清理過期會話"""
        expired_count = 0
        for session_id in list(self.sessions.keys()):
            session = self.sessions[session_id]
            if session.is_expired():
                await self.delete_session(session_id)
                expired_count += 1
        return expired_count
    
    async def _cleanup_loop(self):
        """定期清理過期會話"""
        while True:
            try:
                expired_count = await self.cleanup_expired()
                if expired_count > 0:
                    logger.info(f"Cleaned up {expired_count} expired sessions")
                await asyncio.sleep(300)  # 每5分鐘清理一次
            except Exception as e:
                logger.error(f"Error in cleanup loop: {str(e)}")
                await asyncio.sleep(60)  # 發生錯誤時等待1分鐘
    
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
    
    async def remove_session(self, session_id: str) -> bool:
        """移除會話"""
        if session_id in self.sessions:
            del self.sessions[session_id]
            return True
        return False 