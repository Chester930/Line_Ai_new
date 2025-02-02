from typing import Dict, List, Optional
from dataclasses import dataclass
from datetime import datetime

@dataclass
class Context:
    """對話上下文數據類"""
    messages: List[Dict]
    metadata: Dict
    created_at: datetime
    updated_at: datetime
    
class ContextManager:
    """上下文管理器"""
    VALID_ROLES = {"user", "assistant", "system"}  # 添加有效角色集合
    
    def __init__(self, max_context_length: int = 2000):
        self.max_context_length = max_context_length
        self.current_context: Optional[Context] = None
    
    async def create_context(self) -> Context:
        """創建新的上下文"""
        context = Context(
            messages=[],
            metadata={},
            created_at=datetime.now(),
            updated_at=datetime.now()
        )
        self.current_context = context
        return context
    
    async def add_message(self, role: str, content: str) -> None:
        """添加消息到上下文"""
        # 驗證角色
        if role not in self.VALID_ROLES:
            raise ValueError(f"無效的角色: {role}. 有效角色為: {', '.join(self.VALID_ROLES)}")
        
        # 驗證內容
        if not content or not content.strip():
            raise ValueError("消息內容不能為空")
            
        if not self.current_context:
            await self.create_context()
            
        message = {
            "role": role,
            "content": content,
            "timestamp": datetime.now().isoformat()
        }
        
        self.current_context.messages.append(message)
        self.current_context.updated_at = datetime.now()
        
        # 如果超出最大長度,進行壓縮
        await self._compress_context()
    
    async def _compress_context(self) -> None:
        """壓縮上下文,保留重要信息"""
        if not self.current_context:
            return
            
        total_length = sum(len(m["content"]) for m in self.current_context.messages)
        
        if total_length > self.max_context_length:
            # 保留最新的消息和重要的歷史消息
            important_messages = self.current_context.messages[-5:]  # 最新5條
            self.current_context.messages = important_messages 