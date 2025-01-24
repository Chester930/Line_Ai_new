from typing import Dict, List, Optional
from datetime import datetime
from dataclasses import dataclass, field
from ..ai.base import AIResponse
from ..ai.factory import AIModelFactory, ModelType
from ..utils.logger import logger

@dataclass
class Message:
    """消息數據類"""
    content: str
    role: str
    timestamp: datetime = field(default_factory=datetime.now)
    type: str = "text"
    media_url: Optional[str] = None

@dataclass
class Context:
    """對話上下文"""
    messages: List[Message] = field(default_factory=list)
    metadata: Dict = field(default_factory=dict)
    
    def add_message(self, message: Message):
        """添加消息到上下文"""
        self.messages.append(message)
    
    def get_recent_messages(self, limit: int = 5) -> List[Message]:
        """獲取最近的消息"""
        return self.messages[-limit:] if self.messages else []

class ChatSession:
    """對話會話管理"""
    
    def __init__(self, user_id: str):
        self.user_id = user_id
        self.context = Context()
        self.created_at = datetime.now()
        self.last_active = datetime.now()
    
    async def process_message(
        self,
        message: Message,
        model_type: ModelType = None
    ) -> AIResponse:
        """處理用戶消息"""
        try:
            # 更新活動時間
            self.last_active = datetime.now()
            
            # 添加消息到上下文
            self.context.add_message(message)
            
            # 創建 AI 模型
            model_type = model_type or ModelType(config.settings.default_model)
            model = await AIModelFactory.create(model_type)
            
            # 生成響應
            response = await model.generate(
                prompt=message.content,
                context=[msg.__dict__ for msg in self.context.get_recent_messages()]
            )
            
            # 添加響應到上下文
            if response.text:
                self.context.add_message(Message(
                    content=response.text,
                    role="assistant"
                ))
            
            return response
            
        except Exception as e:
            logger.error(f"處理消息失敗: {str(e)}")
            raise
    
    def is_expired(self, timeout: int = None) -> bool:
        """檢查會話是否過期"""
        timeout = timeout or config.settings.session_timeout
        delta = datetime.now() - self.last_active
        return delta.seconds > timeout

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