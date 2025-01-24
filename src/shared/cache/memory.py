import time
from typing import Any, Dict, Optional, Union
from datetime import timedelta
from .base import BaseCache

class MemoryCache(BaseCache):
    """記憶體快取"""
    
    def __init__(self):
        super().__init__()
        self._cache: Dict[str, tuple] = {}  # {key: (value, expire_time)}
    
    async def get(self, key: str) -> Optional[Any]:
        """獲取快取"""
        try:
            key = self._format_key(key)
            if not await self.exists(key):
                return None
                
            value, expire_time = self._cache[key]
            return value
            
        except Exception as e:
            self.logger.error(f"獲取快取失敗: {str(e)}")
            return None
    
    async def set(
        self,
        key: str,
        value: Any,
        expire: Optional[Union[int, timedelta]] = None
    ) -> bool:
        """設置快取"""
        try:
            key = self._format_key(key)
            expire_seconds = self._get_expire_seconds(expire)
            
            expire_time = None
            if expire_seconds is not None:
                expire_time = time.time() + expire_seconds
                
            self._cache[key] = (value, expire_time)
            return True
            
        except Exception as e:
            self.logger.error(f"設置快取失敗: {str(e)}")
            return False
    
    async def delete(self, key: str) -> bool:
        """刪除快取"""
        try:
            key = self._format_key(key)
            if key in self._cache:
                del self._cache[key]
            return True
            
        except Exception as e:
            self.logger.error(f"刪除快取失敗: {str(e)}")
            return False
    
    async def exists(self, key: str) -> bool:
        """檢查快取是否存在"""
        try:
            key = self._format_key(key)
            if key not in self._cache:
                return False
                
            _, expire_time = self._cache[key]
            if expire_time and time.time() > expire_time:
                await self.delete(key)
                return False
                
            return True
            
        except Exception as e:
            self.logger.error(f"檢查快取失敗: {str(e)}")
            return False
    
    async def clear(self) -> bool:
        """清空快取"""
        try:
            self._cache.clear()
            return True
            
        except Exception as e:
            self.logger.error(f"清空快取失敗: {str(e)}")
            return False 