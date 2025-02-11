import pytest
from datetime import datetime, timedelta
from src.shared.cag.memory import MemoryPool
import asyncio

@pytest.mark.asyncio
class TestMemoryPool:
    @pytest.fixture
    def memory_pool(self):
        return MemoryPool()
    
    async def test_add_and_get_memory(self, memory_pool):
        """測試添加和獲取記憶"""
        # 添加短期記憶
        await memory_pool.add_memory("test_key", "test_value", ttl=60)
        value = await memory_pool.get_memory("test_key")
        assert value == "test_value"
        
        # 添加長期記憶
        await memory_pool.add_memory(
            "long_term_key",
            "long_term_value",
            memory_type="long"
        )
        value = await memory_pool.get_memory(
            "long_term_key",
            memory_type="long"
        )
        assert value == "long_term_value"
    
    async def test_memory_expiration(self, memory_pool):
        """測試記憶過期"""
        # 添加即將過期的記憶
        await memory_pool.add_memory("expire_key", "expire_value", ttl=0.1)
        
        # 等待過期
        await asyncio.sleep(0.2)
        
        # 應該無法獲取已過期的記憶
        value = await memory_pool.get_memory("expire_key")
        assert value is None
    
    async def test_clear_expired(self, memory_pool):
        """測試清理過期記憶"""
        # 添加多個記憶，部分設置較短的過期時間
        await memory_pool.add_memory("key1", "value1", ttl=0.1)
        await memory_pool.add_memory("key2", "value2", ttl=60)
        
        # 等待部分記憶過期
        await asyncio.sleep(0.2)
        
        # 清理過期記憶
        await memory_pool.clear_expired()
        
        # 驗證結果
        assert await memory_pool.get_memory("key1") is None
        assert await memory_pool.get_memory("key2") == "value2"
    
    async def test_memory_types(self, memory_pool):
        """測試不同類型的記憶"""
        # 測試不同類型的值
        test_values = [
            "string value",
            123,
            {"key": "value"},
            ["list", "of", "items"],
            True
        ]
        
        for i, value in enumerate(test_values):
            key = f"test_key_{i}"
            await memory_pool.add_memory(key, value)
            result = await memory_pool.get_memory(key)
            assert result == value 