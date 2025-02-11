from abc import ABC, abstractmethod
from typing import Any, Optional, Union
from datetime import timedelta
from ..utils.logger import logger

class BaseCache(ABC):
    """快取基類"""
    
    def __init__(self):
        self.logger = logger
    
    @abstractmethod
    async def get(self, key: str) -> Optional[Any]:
        """獲取快取"""
        pass
    
    @abstractmethod
    async def set(
        self,
        key: str,
        value: Any,
        expire: Optional[Union[int, timedelta]] = None
    ) -> bool:
        """設置快取"""
        pass
    
    @abstractmethod
    async def delete(self, key: str) -> bool:
        """刪除快取"""
        pass
    
    @abstractmethod
    async def exists(self, key: str) -> bool:
        """檢查快取是否存在"""
        pass
    
    @abstractmethod
    async def clear(self) -> bool:
        """清空快取"""
        pass
    
    def _format_key(self, key: str) -> str:
        """格式化鍵名"""
        return f"cache:{key}"
    
    def _get_expire_seconds(
        self,
        expire: Optional[Union[int, timedelta]]
    ) -> Optional[int]:
        """獲取過期秒數"""
        if expire is None:
            return None
        if isinstance(expire, timedelta):
            return int(expire.total_seconds())
        return expire 