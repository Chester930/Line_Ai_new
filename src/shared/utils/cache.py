from typing import Any, Optional
import redis

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