from typing import Dict, List, Optional
from datetime import datetime, timedelta
from dataclasses import dataclass, field
from .session import Message
from ..utils.logger import logger

@dataclass
class Memory:
    """記憶數據類"""
    content: str
    importance: float
    timestamp: datetime = field(default_factory=datetime.now)
    metadata: Dict = field(default_factory=dict)

class MemoryManager:
    """記憶管理器"""
    
    def __init__(self, capacity: int = 100):
        self.capacity = capacity
        self.memories: List[Memory] = []
        self.importance_threshold = 0.5
    
    def add_memory(self, content: str, importance: float = 0.0, metadata: Dict = None):
        """添加記憶"""
        try:
            if len(self.memories) >= self.capacity:
                self._cleanup_memories()
            
            memory = Memory(
                content=content,
                importance=importance,
                metadata=metadata or {}
            )
            self.memories.append(memory)
            
        except Exception as e:
            logger.error(f"添加記憶失敗: {str(e)}")
    
    def get_relevant_memories(
        self,
        query: str,
        limit: int = 5,
        min_importance: float = None
    ) -> List[Memory]:
        """獲取相關記憶"""
        try:
            filtered = self.memories
            
            # 根據重要性過濾
            if min_importance is not None:
                filtered = [m for m in filtered if m.importance >= min_importance]
            
            # TODO: 實現相關性排序
            # 當前簡單返回最近的記憶
            return sorted(
                filtered,
                key=lambda x: x.timestamp,
                reverse=True
            )[:limit]
            
        except Exception as e:
            logger.error(f"獲取記憶失敗: {str(e)}")
            return []
    
    def _cleanup_memories(self):
        """清理記憶"""
        if not self.memories:
            return
            
        # 保留重要的記憶
        important = [m for m in self.memories if m.importance >= self.importance_threshold]
        
        # 如果重要記憶太多，根據時間排序
        if len(important) >= self.capacity:
            important.sort(key=lambda x: x.timestamp, reverse=True)
            self.memories = important[:self.capacity]
        else:
            # 填充剩餘空間
            recent = sorted(
                [m for m in self.memories if m.importance < self.importance_threshold],
                key=lambda x: x.timestamp,
                reverse=True
            )
            self.memories = important + recent[:self.capacity - len(important)]
    
    def clear_old_memories(self, days: int = 30):
        """清理舊記憶"""
        cutoff = datetime.now() - timedelta(days=days)
        self.memories = [
            m for m in self.memories
            if m.timestamp > cutoff or m.importance >= self.importance_threshold
        ] 