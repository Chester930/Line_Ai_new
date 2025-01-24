import json
from typing import Any, Optional, Union
from datetime import timedelta
import aioredis
from .base import BaseCache

class RedisCache(BaseCache):
    """Redis 快取"""
    
    def __init__(self, redis_url: str):
        super().__init__()
        self.redis = aioredis.from_url(redis_url)
    
    async def get(self, key: str) -> Optional[Any]:
        """獲取快取"""
        try:
            key = self._format_key(key)
            value = await self.redis.get(key)
            
            if value is None:
                return None
                
            return json.loads(value)
            
        except Exception as e:
            self.logger.error(f"獲取 Redis 快取失敗: {str(e)}")
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
            value = json.dumps(value)
            
            if expire:
                expire_seconds = self._get_expire_seconds(expire)
                await self.redis.setex(key, expire_seconds, value)
            else:
                await self.redis.set(key, value)
                
            return True
            
        except Exception as e:
            self.logger.error(f"設置 Redis 快取失敗: {str(e)}")
            return False
    
    async def delete(self, key: str) -> bool:
        """刪除快取"""
        try:
            key = self._format_key(key)
            await self.redis.delete(key)
            return True
            
        except Exception as e:
            self.logger.error(f"刪除 Redis 快取失敗: {str(e)}")
            return False
    
    async def exists(self, key: str) -> bool:
        """檢查快取是否存在"""
        try:
            key = self._format_key(key)
            return await self.redis.exists(key) > 0
            
        except Exception as e:
            self.logger.error(f"檢查 Redis 快取失敗: {str(e)}")
            return False
    
    async def clear(self) -> bool:
        """清空快取"""
        try:
            await self.redis.flushdb()
            return True
            
        except Exception as e:
            self.logger.error(f"清空 Redis 快取失敗: {str(e)}")
            return False
    
    async def close(self):
        """關閉連接"""
        await self.redis.close() 