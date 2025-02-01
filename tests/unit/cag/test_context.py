import pytest
from datetime import datetime
from src.shared.cag.context import ContextManager, Context

@pytest.mark.asyncio
class TestContextManager:
    async def test_create_context(self):
        manager = ContextManager()
        context = await manager.create_context()
        
        assert isinstance(context, Context)
        assert len(context.messages) == 0
        assert isinstance(context.created_at, datetime)
    
    async def test_add_message(self):
        manager = ContextManager()
        await manager.add_message("user", "Hello")
        
        assert len(manager.current_context.messages) == 1
        assert manager.current_context.messages[0]["role"] == "user"
        assert manager.current_context.messages[0]["content"] == "Hello"
    
    async def test_context_compression(self):
        manager = ContextManager(max_context_length=10)
        
        # 添加超過長度限制的消息
        await manager.add_message("user", "This is a long message")
        
        # 驗證是否進行了壓縮
        assert len(manager.current_context.messages) <= 5 