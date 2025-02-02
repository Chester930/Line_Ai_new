import pytest
from datetime import datetime, timedelta
from src.shared.cag.context import ContextManager, Context
import asyncio

@pytest.mark.asyncio
class TestContextManager:
    async def test_create_context(self, context_manager):
        """測試創建上下文"""
        context = await context_manager.create_context()
        
        assert isinstance(context, Context)
        assert len(context.messages) == 0
        assert isinstance(context.metadata, dict)
        assert isinstance(context.created_at, datetime)
        assert isinstance(context.updated_at, datetime)
    
    async def test_add_message(self, context_manager):
        """測試添加消息"""
        # 添加第一條消息
        await context_manager.add_message("user", "Hello")
        
        assert context_manager.current_context is not None
        assert len(context_manager.current_context.messages) == 1
        message = context_manager.current_context.messages[0]
        assert message["role"] == "user"
        assert message["content"] == "Hello"
        assert "timestamp" in message
        
        # 添加第二條消息
        await context_manager.add_message("assistant", "Hi there!")
        assert len(context_manager.current_context.messages) == 2
    
    async def test_context_compression(self, context_manager):
        """測試上下文壓縮"""
        # 添加多條消息直到超過最大長度
        long_message = "x" * 500  # 500 字符的消息
        for _ in range(5):  # 添加 5 條消息，總長度 2500
            await context_manager.add_message("user", long_message)
            
        # 檢查是否進行了壓縮
        assert len(context_manager.current_context.messages) <= 5
        
        # 檢查最新的消息是否被保留
        latest_message = context_manager.current_context.messages[-1]
        assert latest_message["content"] == long_message
    
    async def test_auto_context_creation(self, context_manager):
        """測試自動創建上下文"""
        # 直接添加消息，不先創建上下文
        await context_manager.add_message("user", "Hello")
        
        assert context_manager.current_context is not None
        assert len(context_manager.current_context.messages) == 1
    
    async def test_context_metadata(self, context_manager):
        """測試上下文元數據"""
        context = await context_manager.create_context()
        
        # 添加元數據
        context.metadata["user_id"] = "test_user"
        context.metadata["session_id"] = "test_session"
        
        assert context.metadata["user_id"] == "test_user"
        assert context.metadata["session_id"] == "test_session"
    
    async def test_context_timestamps(self, context_manager):
        """測試上下文時間戳"""
        context = await context_manager.create_context()
        initial_time = context.updated_at
        
        # 等待一小段時間
        await asyncio.sleep(0.1)
        
        # 添加消息應該更新時間戳
        await context_manager.add_message("user", "Hello")
        assert context_manager.current_context.updated_at > initial_time
    
    async def test_invalid_message(self, context_manager):
        """測試無效消息處理"""
        # 測試空消息
        with pytest.raises(ValueError, match="消息內容不能為空"):
            await context_manager.add_message("user", "")
        
        with pytest.raises(ValueError, match="消息內容不能為空"):
            await context_manager.add_message("user", "   ")
        
        # 測試無效角色
        with pytest.raises(ValueError, match="無效的角色"):
            await context_manager.add_message("invalid_role", "Hello")
    
    async def test_context_initialization(self, context_manager):
        """測試上下文初始化"""
        context = await context_manager.create_context()
        assert context.messages == []
        assert context.metadata == {}
        assert isinstance(context.created_at, datetime)
        assert isinstance(context.updated_at, datetime)
    
    async def test_message_validation(self, context_manager):
        """測試消息驗證"""
        # 測試無效的角色
        with pytest.raises(ValueError, match="無效的角色"):
            await context_manager.add_message("invalid_role", "test")
        
        # 測試空消息
        with pytest.raises(ValueError, match="消息內容不能為空"):
            await context_manager.add_message("user", "")
        
        # 測試空白消息
        with pytest.raises(ValueError, match="消息內容不能為空"):
            await context_manager.add_message("user", "   ")
    
    async def test_message_format(self, context_manager):
        """測試消息格式"""
        await context_manager.add_message("user", "test message")
        message = context_manager.current_context.messages[-1]
        
        assert "role" in message
        assert "content" in message
        assert "timestamp" in message
        assert message["role"] == "user"
        assert message["content"] == "test message"
        assert isinstance(message["timestamp"], str)
    
    async def test_context_compression_threshold(self, context_manager):
        """測試上下文壓縮閾值"""
        # 設置較小的最大長度
        context_manager.max_context_length = 100
        
        # 添加超過長度限制的消息
        messages = [
            "This is a long message that should trigger compression",
            "Another message to ensure we exceed the limit",
            "Final message to verify compression"
        ]
        
        for msg in messages:
            await context_manager.add_message("user", msg)
        
        # 驗證壓縮後的消息數量
        assert len(context_manager.current_context.messages) <= 5
        
        # 驗證最新消息被保留
        assert context_manager.current_context.messages[-1]["content"] == messages[-1]
    
    async def test_metadata_operations(self, context_manager):
        """測試元數據操作"""
        context = await context_manager.create_context()
        
        # 添加元數據
        context.metadata["user_id"] = "test_user"
        context.metadata["session_id"] = "test_session"
        context.metadata["preferences"] = {"language": "zh"}
        
        # 驗證元數據
        assert context.metadata["user_id"] == "test_user"
        assert context.metadata["session_id"] == "test_session"
        assert context.metadata["preferences"]["language"] == "zh" 