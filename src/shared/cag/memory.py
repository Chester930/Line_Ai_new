from typing import Dict, Any, Optional
from datetime import datetime, timedelta

class MemoryPool:
    """記憶池系統"""
    def __init__(self):
        self.short_term: Dict[str, Any] = {}  # 短期記憶
        self.long_term: Dict[str, Any] = {}   # 長期記憶
        self.ttl: Dict[str, datetime] = {}    # 記憶過期時間
    
    async def add_memory(
        self, 
        key: str, 
        value: Any, 
        memory_type: str = "short",
        ttl: Optional[int] = None  # 過期時間(秒)
    ) -> None:
        """添加記憶"""
        if memory_type == "short":
            self.short_term[key] = value
            if ttl:
                self.ttl[key] = datetime.now() + timedelta(seconds=ttl)
        else:
            self.long_term[key] = value
    
    async def get_memory(
        self, 
        key: str, 
        memory_type: str = "short"
    ) -> Optional[Any]:
        """獲取記憶"""
        # 檢查是否過期
        if key in self.ttl and datetime.now() > self.ttl[key]:
            if memory_type == "short":
                self.short_term.pop(key, None)
            self.ttl.pop(key, None)
            return None
            
        if memory_type == "short":
            return self.short_term.get(key)
        return self.long_term.get(key)
    
    async def clear_expired(self) -> None:
        """清理過期記憶"""
        now = datetime.now()
        expired = [k for k, v in self.ttl.items() if now > v]
        for key in expired:
            self.short_term.pop(key, None)
            self.ttl.pop(key, None) 