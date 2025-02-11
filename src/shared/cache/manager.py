from typing import Optional, Dict, Type
from enum import Enum
from .base import BaseCache
from .memory import MemoryCache
from .redis import RedisCache
from ..utils.logger import logger

class CacheType(str, Enum):
    """快取類型"""
    MEMORY = "memory"
    REDIS = "redis"

class CacheManager:
    """快取管理器"""
    
    def __init__(self):
        self._caches: Dict[str, BaseCache] = {}
        self._default_type = CacheType.MEMORY
    
    def get_cache(
        self,
        cache_type: Optional[CacheType] = None,
        **kwargs
    ) -> BaseCache:
        """獲取快取實例"""
        cache_type = cache_type or self._default_type
        
        # 檢查是否已存在實例
        if cache_type.value in self._caches:
            return self._caches[cache_type.value]
        
        # 創建新實例
        cache = self._create_cache(cache_type, **kwargs)
        self._caches[cache_type.value] = cache
        return cache
    
    def _create_cache(
        self,
        cache_type: CacheType,
        **kwargs
    ) -> BaseCache:
        """創建快取實例"""
        try:
            if cache_type == CacheType.MEMORY:
                return MemoryCache()
            elif cache_type == CacheType.REDIS:
                redis_url = kwargs.get("redis_url")
                if not redis_url:
                    raise ValueError("Redis URL 未提供")
                return RedisCache(redis_url)
            else:
                raise ValueError(f"不支持的快取類型: {cache_type}")
                
        except Exception as e:
            logger.error(f"創建快取實例失敗: {str(e)}")
            # 如果創建失敗，返回記憶體快取作為後備
            return MemoryCache()
    
    async def clear_all(self):
        """清空所有快取"""
        for cache in self._caches.values():
            await cache.clear()
    
    async def close_all(self):
        """關閉所有快取連接"""
        for cache in self._caches.values():
            if hasattr(cache, 'close'):
                await cache.close()
        self._caches.clear()

# 創建全局快取管理器實例
cache_manager = CacheManager() 