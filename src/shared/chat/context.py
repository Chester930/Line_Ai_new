from typing import List, Dict, Any
from datetime import datetime

class Context:
    """對話上下文"""
    def __init__(self):
        self.messages: List[Dict[str, str]] = []
        self.created_at = datetime.now()
        self.last_updated = datetime.now()
    
    def add_message(self, role: str, content: str) -> None:
        """添加消息"""
        self.messages.append({
            "role": role,
            "content": content,
            "timestamp": datetime.now().isoformat()
        })
        self.last_updated = datetime.now()
    
    def get_messages(self) -> List[Dict[str, str]]:
        """獲取所有消息"""
        return self.messages
    
    def clear(self) -> None:
        """清除所有消息"""
        self.messages = []
        self.last_updated = datetime.now()
    
    def get_last_message(self) -> Dict[str, str]:
        """獲取最後一條消息"""
        return self.messages[-1] if self.messages else {}
    
    def get_context_age(self) -> float:
        """獲取上下文年齡（分鐘）"""
        delta = datetime.now() - self.created_at
        return delta.total_seconds() / 60

class ContextManager:
    """上下文管理器"""
    def __init__(self):
        self.contexts: Dict[str, Context] = {}
    
    def get_or_create_context(self, user_id: str) -> Context:
        """獲取或創建上下文"""
        if user_id not in self.contexts:
            self.contexts[user_id] = Context()
        return self.contexts[user_id]
    
    def clear_context(self, user_id: str) -> None:
        """清除指定用戶的上下文"""
        if user_id in self.contexts:
            self.contexts[user_id].clear()
    
    def remove_context(self, user_id: str) -> None:
        """移除指定用戶的上下文"""
        if user_id in self.contexts:
            del self.contexts[user_id] 