from typing import Dict, Optional
from datetime import datetime
from .session import ChatSession
from .context import ContextManager
from .handlers.manager import MessageHandlerManager
from ..ai.base import ModelType
from ..utils.logger import logger

class ChatManager:
    """對話管理器"""
    
    def __init__(self):
        self.sessions: Dict[str, ChatSession] = {}
        self.handlers = MessageHandlerManager()
        self.session_timeout = 3600  # 1小時
    
    async def get_or_create_session(self, user_id: str) -> ChatSession:
        """獲取或創建會話"""
        try:
            session = self.sessions.get(user_id)
            
            # 檢查會話是否存在且未過期
            if session and not session.is_expired(self.session_timeout):
                return session
            
            # 創建新會話
            session = ChatSession(user_id)
            self.sessions[user_id] = session
            return session
            
        except Exception as e:
            logger.error(f"獲取會話失敗: {str(e)}")
            raise
    
    async def process_message(
        self,
        user_id: str,
        message_type: str,
        content: str,
        metadata: Dict = None
    ) -> Dict:
        """處理消息"""
        try:
            # 獲取會話
            session = await self.get_or_create_session(user_id)
            
            # 創建消息
            message = Message(
                content=content,
                role="user",
                type=message_type,
                metadata=metadata or {}
            )
            
            # 處理消息
            handler = self.handlers._handlers.get(message_type)
            if not handler:
                raise ValueError(f"未知的消息類型: {message_type}")
            
            result = await handler.handle(message)
            
            # 更新上下文
            if result.get("success"):
                await session.context.add_to_history(
                    role="user",
                    content=content,
                    importance=metadata.get("importance", 0.0)
                )
                
                if result.get("response"):
                    await session.context.add_to_history(
                        role="assistant",
                        content=result["response"],
                        importance=0.5
                    )
            
            return result
            
        except Exception as e:
            logger.error(f"處理消息失敗: {str(e)}")
            return {
                "success": False,
                "error": str(e)
            }
    
    async def cleanup_sessions(self):
        """清理過期會話"""
        try:
            expired = [
                user_id
                for user_id, session in self.sessions.items()
                if session.is_expired(self.session_timeout)
            ]
            
            for user_id in expired:
                del self.sessions[user_id]
                
        except Exception as e:
            logger.error(f"清理會話失敗: {str(e)}") 