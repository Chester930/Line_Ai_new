from typing import Dict, Optional, Any
from datetime import datetime
from .context import Context, ContextManager
from ..ai.factory import ModelFactory
from ..utils.logger import logger

class ChatSession:
    """聊天會話"""
    def __init__(self, user_id: str):
        self.user_id = user_id
        self.current_model = 'gemini'
        self.model_factory = ModelFactory()
        self.context_manager = ContextManager()
        self._initialize()
    
    def _initialize(self):
        """初始化會話"""
        try:
            self.model = self.model_factory.create_model(self.current_model)
            self.context = self.context_manager.get_or_create_context(self.user_id)
        except Exception as e:
            logger.error(f"初始化會話失敗: {str(e)}")
            raise
    
    def send_message(self, message: str) -> str:
        """發送消息"""
        try:
            self.context.add_message("user", message)
            response = self.model.generate_response(self.context.get_messages())
            self.context.add_message("assistant", response)
            return response
        except Exception as e:
            logger.error(f"發送消息失敗: {str(e)}")
            raise
    
    def switch_model(self, model_type: str) -> bool:
        """切換模型"""
        try:
            self.model = self.model_factory.create_model(model_type)
            self.current_model = model_type
            return True
        except Exception as e:
            logger.error(f"切換模型失敗: {str(e)}")
            return False
    
    def clear_context(self) -> None:
        """清除上下文"""
        self.context.clear()

class SessionManager:
    """會話管理器"""
    def __init__(self):
        self.sessions: Dict[str, ChatSession] = {}
    
    def get_session(self, user_id: str) -> ChatSession:
        """獲取或創建會話"""
        if user_id not in self.sessions:
            self.sessions[user_id] = ChatSession(user_id)
        return self.sessions[user_id]
    
    def clear_session(self, user_id: str) -> None:
        """清除會話"""
        if user_id in self.sessions:
            del self.sessions[user_id]

# 全局會話管理器實例
session_manager = SessionManager() 