from typing import List, Dict, Any, Optional
from datetime import datetime
from .session import Message
from ..utils.logger import logger
from dataclasses import dataclass, field
from .memory import MemoryManager

@dataclass
class ContextState:
    """上下文狀態"""
    topic: Optional[str] = None
    mood: Optional[str] = None
    language: str = "zh-TW"
    metadata: Dict = field(default_factory=dict)

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
        self.state = ContextState()
        self.memory = MemoryManager()
        self.conversation_history: List[Dict] = []
        self.max_history_length = 50
    
    async def update_state(self, **kwargs):
        """更新上下文狀態"""
        try:
            for key, value in kwargs.items():
                if hasattr(self.state, key):
                    setattr(self.state, key, value)
                else:
                    self.state.metadata[key] = value
        except Exception as e:
            logger.error(f"更新上下文狀態失敗: {str(e)}")
    
    async def add_to_history(
        self,
        role: str,
        content: str,
        importance: float = 0.0
    ):
        """添加對話歷史"""
        try:
            # 添加到對話歷史
            entry = {
                "role": role,
                "content": content,
                "timestamp": datetime.now(),
                "metadata": {
                    "topic": self.state.topic,
                    "mood": self.state.mood
                }
            }
            self.conversation_history.append(entry)
            
            # 維護歷史長度
            if len(self.conversation_history) > self.max_history_length:
                self._cleanup_history()
            
            # 添加到記憶
            if importance > 0:
                self.memory.add_memory(
                    content=content,
                    importance=importance,
                    metadata={"role": role, "topic": self.state.topic}
                )
                
        except Exception as e:
            logger.error(f"添加對話歷史失敗: {str(e)}")
    
    async def get_context_summary(self) -> Dict:
        """獲取上下文摘要"""
        return {
            "state": self.state.__dict__,
            "recent_history": self.conversation_history[-5:],
            "relevant_memories": self.memory.get_relevant_memories(
                query=self.state.topic or "",
                limit=3
            )
        }
    
    def _cleanup_history(self):
        """清理歷史記錄"""
        # 保留重要對話
        important = [
            entry for entry in self.conversation_history
            if entry.get("metadata", {}).get("importance", 0) >= 0.5
        ]
        
        # 保留最近對話
        recent = self.conversation_history[-self.max_history_length//2:]
        
        # 合併並去重
        self.conversation_history = list({
            entry["timestamp"]: entry
            for entry in (important + recent)
        }.values())
        
        # 按時間排序
        self.conversation_history.sort(key=lambda x: x["timestamp"])

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