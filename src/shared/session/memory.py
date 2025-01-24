from typing import Dict, List, Optional, Any
from datetime import datetime
from .base import BaseSession, Message
from ..utils.logger import logger

class MemorySession(BaseSession):
    """記憶體會話"""
    
    async def add_message(self, message: Message) -> bool:
        """添加消息"""
        try:
            # 更新活動時間
            self.update_activity()
            
            # 添加消息
            self.messages.append(message)
            
            # 如果超過最大消息數，刪除最舊的消息
            while len(self.messages) > self.max_messages:
                self.messages.pop(0)
                
            return True
            
        except Exception:
            return False
    
    async def get_messages(
        self,
        limit: Optional[int] = None
    ) -> List[Message]:
        """獲取消息"""
        self.update_activity()
        
        if limit is None or limit >= len(self.messages):
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

class MemorySessionManager:
    """記憶體會話管理器"""
    
    def __init__(self):
        self._sessions: Dict[str, MemorySession] = {}
    
    async def get_session(
        self,
        session_id: str
    ) -> Optional[MemorySession]:
        """獲取會話"""
        return self._sessions.get(session_id)
    
    async def create_session(
        self,
        user_id: str,
        metadata: Optional[Dict[str, Any]] = None
    ) -> MemorySession:
        """創建會話"""
        session = MemorySession(
            user_id=user_id,
            metadata=metadata or {}
        )
        self._sessions[session.session_id] = session
        logger.info(
            f"已創建會話: {session.session_id} "
            f"(用戶: {user_id})"
        )
        return session
    
    async def save_session(
        self,
        session: MemorySession
    ) -> bool:
        """保存會話"""
        try:
            self._sessions[session.session_id] = session
            logger.debug(
                f"已保存會話: {session.session_id} "
                f"(消息數: {len(session.messages)})"
            )
            return True
        except Exception as e:
            logger.error(f"保存會話失敗: {str(e)}")
            return False
    
    async def delete_session(
        self,
        session_id: str
    ) -> bool:
        """刪除會話"""
        try:
            if session_id in self._sessions:
                del self._sessions[session_id]
                logger.info(f"已刪除會話: {session_id}")
                return True
            return False
        except Exception as e:
            logger.error(f"刪除會話失敗: {str(e)}")
            return False
    
    async def list_sessions(
        self,
        user_id: Optional[str] = None
    ) -> List[MemorySession]:
        """列出會話"""
        if user_id:
            return [
                session for session in self._sessions.values()
                if session.user_id == user_id
            ]
        return list(self._sessions.values()) 