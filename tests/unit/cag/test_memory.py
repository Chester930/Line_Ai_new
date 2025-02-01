import pytest
from datetime import datetime, timedelta
from src.shared.cag.memory import MemoryPool
import asyncio

@pytest.mark.asyncio
class TestMemoryPool:
    async def test_add_and_get_memory(self):
        pool = MemoryPool()
        
        # 測試短期記憶
        await pool.add_memory("test_key", "test_value")
        value = await pool.get_memory("test_key")
        assert value == "test_value"
        
        # 測試長期記憶
        await pool.add_memory("long_key", "long_value", memory_type="long")
        value = await pool.get_memory("long_key", memory_type="long")
        assert value == "long_value"
    
    async def test_memory_expiration(self):
        pool = MemoryPool()
        
        # 添加一個1秒後過期的記憶
        await pool.add_memory("expire_key", "expire_value", ttl=1)
        
        # 立即獲取應該存在
        value = await pool.get_memory("expire_key")
        assert value == "expire_value"
        
        # 等待過期
        await asyncio.sleep(1.1)
        
        # 獲取應該返回None
        value = await pool.get_memory("expire_key")
        assert value is None
    
    async def test_clear_expired(self):
        pool = MemoryPool()
        
        # 添加多個過期記憶
        await pool.add_memory("key1", "value1", ttl=1)
        await pool.add_memory("key2", "value2", ttl=1)
        
        # 等待過期
        await asyncio.sleep(1.1)
        
        # 清理過期記憶
        await pool.clear_expired()
        
        # 驗證是否已清理
        assert await pool.get_memory("key1") is None
        assert await pool.get_memory("key2") is None 