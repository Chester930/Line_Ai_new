from typing import Any, Optional
import redis
import asyncio

class CacheManager:
    """快取管理器"""
    def __init__(self):
        self.redis = redis.Redis()
        
    async def get(self, key: str) -> Optional[Any]:
        """獲取快取"""
        return self.redis.get(key)
        
    async def set(self, key: str, value: Any, ttl: int = 3600):
        """設置快取"""
        self.redis.set(key, value, ex=ttl)

class ResponseCache:
    def __init__(self, ttl: int = 300):
        self.ttl = ttl
        self._cache = {}
    
    async def get_or_set(self, key: str, coroutine):
        """快取非同步查詢結果"""
        if key in self._cache:
            return self._cache[key]
        
        result = await coroutine
        self._cache[key] = result
        asyncio.get_event_loop().call_later(self.ttl, self._expire_key, key)
        return result 