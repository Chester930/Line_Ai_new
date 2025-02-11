import pytest
from datetime import timedelta
from src.shared.cache.memory import MemoryCache
from src.shared.cache.redis import RedisCache

@pytest.fixture
def memory_cache():
    """記憶體快取"""
    return MemoryCache()

@pytest.fixture
async def redis_cache():
    """Redis 快取"""
    cache = RedisCache("redis://localhost")
    yield cache
    await cache.clear()
    await cache.close()

@pytest.mark.asyncio
async def test_memory_cache_basic(memory_cache):
    """測試記憶體快取基本操作"""
    # 設置快取
    assert await memory_cache.set("test_key", "test_value")
    
    # 獲取快取
    assert await memory_cache.get("test_key") == "test_value"
    
    # 檢查存在
    assert await memory_cache.exists("test_key")
    
    # 刪除快取
    assert await memory_cache.delete("test_key")
    assert not await memory_cache.exists("test_key")

@pytest.mark.asyncio
async def test_memory_cache_expiration(memory_cache):
    """測試記憶體快取過期"""
    # 設置快取（1秒過期）
    await memory_cache.set("test_key", "test_value", expire=1)
    
    # 立即檢查
    assert await memory_cache.exists("test_key")
    
    # 等待過期
    await asyncio.sleep(1.1)
    assert not await memory_cache.exists("test_key")

@pytest.mark.asyncio
async def test_redis_cache_basic(redis_cache):
    """測試 Redis 快取基本操作"""
    # 設置快取
    assert await redis_cache.set("test_key", {"name": "test"})
    
    # 獲取快取
    value = await redis_cache.get("test_key")
    assert value == {"name": "test"}
    
    # 檢查存在
    assert await redis_cache.exists("test_key")
    
    # 刪除快取
    assert await redis_cache.delete("test_key")
    assert not await redis_cache.exists("test_key")

@pytest.mark.asyncio
async def test_redis_cache_expiration(redis_cache):
    """測試 Redis 快取過期"""
    # 設置快取（1秒過期）
    await redis_cache.set(
        "test_key",
        "test_value",
        expire=timedelta(seconds=1)
    )
    
    # 立即檢查
    assert await redis_cache.exists("test_key")
    
    # 等待過期
    await asyncio.sleep(1.1)
    assert not await redis_cache.exists("test_key") 