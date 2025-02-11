import pytest
from datetime import timedelta
from src.shared.cache.decorators import cache
from src.shared.cache.manager import CacheManager, CacheType
from typing import Optional
from src.shared.utils.types import Callable
from src.shared.cache.base import Cache

class TestService:
    """測試服務類"""
    
    @cache(expire=60)
    async def get_data(self, key: str) -> dict:
        """獲取數據"""
        return {"key": key, "value": "test"}
    
    @cache(expire=timedelta(minutes=1), key_prefix="user")
    async def get_user(self, user_id: int) -> dict:
        """獲取用戶"""
        return {"id": user_id, "name": "test_user"}
    
    @cache(expire=30, cache_null=True)
    async def get_nullable(self, key: str) -> Optional[str]:
        """可能返回空值的方法"""
        return None

@pytest.fixture
def cache_manager():
    """快取管理器"""
    return CacheManager()

@pytest.fixture
def test_service():
    """測試服務"""
    return TestService()

@pytest.mark.asyncio
async def test_cache_decorator_basic(cache_manager, test_service):
    """測試基本快取裝飾器"""
    cache_instance = cache_manager.get_cache(CacheType.MEMORY)
    
    # 首次調用
    result1 = await test_service.get_data(
        "test",
        cache_instance=cache_instance
    )
    assert result1 == {"key": "test", "value": "test"}
    
    # 快取命中
    result2 = await test_service.get_data(
        "test",
        cache_instance=cache_instance
    )
    assert result2 == result1

@pytest.mark.asyncio
async def test_cache_with_prefix(cache_manager, test_service):
    """測試帶前綴的快取"""
    cache_instance = cache_manager.get_cache(CacheType.MEMORY)
    
    # 調用帶前綴的方法
    result = await test_service.get_user(
        1,
        cache_instance=cache_instance
    )
    assert result == {"id": 1, "name": "test_user"}

@pytest.mark.asyncio
async def test_cache_null_values(cache_manager, test_service):
    """測試空值快取"""
    cache_instance = cache_manager.get_cache(CacheType.MEMORY)
    
    # 首次調用
    result1 = await test_service.get_nullable(
        "test",
        cache_instance=cache_instance
    )
    assert result1 is None
    
    # 快取命中
    result2 = await test_service.get_nullable(
        "test",
        cache_instance=cache_instance
    )
    assert result2 is None

@pytest.mark.asyncio
async def test_cache_manager_types(cache_manager):
    """測試快取管理器類型"""
    # 記憶體快取
    memory_cache = cache_manager.get_cache(CacheType.MEMORY)
    assert memory_cache is not None
    
    # Redis 快取（應該返回記憶體快取作為後備）
    redis_cache = cache_manager.get_cache(CacheType.REDIS)
    assert redis_cache is not None

@pytest.mark.asyncio
async def test_cache_manager_cleanup(cache_manager):
    """測試快取管理器清理"""
    # 獲取快取實例
    cache = cache_manager.get_cache(CacheType.MEMORY)
    
    # 設置一些數據
    await cache.set("test", "value")
    assert await cache.exists("test")
    
    # 清理所有快取
    await cache_manager.clear_all()
    assert not await cache.exists("test")
    
    # 關閉所有連接
    await cache_manager.close_all() 