import pytest
from datetime import datetime, timedelta
from src.shared.session.base import Message, Session
from src.shared.session.memory import MemorySessionManager
from src.shared.session.factory import SessionFactory
import asyncio

@pytest.fixture
def session_factory():
    """測試會話工廠的 fixture"""
    return SessionFactory()

@pytest.mark.asyncio
async def test_concurrent_session_access():
    """測試並發會話訪問"""
    manager = MemorySessionManager()
    session = await manager.create_session("test_user")
    
    async def add_messages(count: int):
        for i in range(count):
            message = Message("test_user", f"Message {i}")
            session.add_message(message)
            await manager.save_session(session)
            await asyncio.sleep(0.1)
    
    # 同時運行多個協程來測試並發訪問
    tasks = [
        add_messages(5),
        add_messages(5)
    ]
    await asyncio.gather(*tasks)
    
    # 驗證結果
    updated_session = await manager.get_session(session.id)
    assert len(updated_session.messages) == 10

@pytest.mark.asyncio
async def test_session_cleanup():
    """測試過期會話清理"""
    manager = MemorySessionManager()
    
    # 創建一些會話，包括過期的
    session1 = await manager.create_session("user1", ttl=1)
    session2 = await manager.create_session("user2", ttl=3600)
    
    # 等待第一個會話過期
    await asyncio.sleep(2)
    
    # 驗證過期會話被清理
    assert await manager.get_session(session1.id) is None
    assert await manager.get_session(session2.id) is not None

def test_session_metadata_management():
    """測試會話元數據管理"""
    session = Session("test_session", "test_user")
    
    # 測試元數據更新
    metadata = {
        "last_intent": "greeting",
        "user_preference": "casual",
        "language": "zh-TW"
    }
    session.update_metadata(metadata)
    
    assert session.metadata["last_intent"] == "greeting"
    assert session.metadata["user_preference"] == "casual"
    
    # 測試元數據移除
    session.remove_metadata("last_intent")
    assert "last_intent" not in session.metadata

@pytest.mark.asyncio
async def test_session_factory_creation():
    """測試會話工廠創建不同類型的會話"""
    factory = SessionFactory()
    
    # 測試創建記憶體會話
    memory_session = await factory.create_session(
        session_type="memory",
        user_id="test_user",
        metadata={"type": "memory"}
    )
    assert memory_session is not None
    assert memory_session.metadata["type"] == "memory"
    
    # 測試無效會話類型
    with pytest.raises(ValueError):
        await factory.create_session(
            session_type="invalid",
            user_id="test_user"
        )

@pytest.mark.asyncio
async def test_session_message_history():
    """測試會話歷史記錄管理"""
    manager = MemorySessionManager()
    session = await manager.create_session("test_user")
    
    # 添加不同類型的消息
    messages = [
        Message("test_user", "Text message", message_type="text"),
        Message("test_user", "image_url", message_type="image"),
        Message("test_user", "location_data", message_type="location")
    ]
    
    for msg in messages:
        session.add_message(msg)
    
    # 測試按類型過濾消息
    text_messages = session.get_messages(message_type="text")
    assert len(text_messages) == 1
    assert text_messages[0].type == "text"
    
    # 測試時間範圍過濾
    time_range_messages = session.get_messages(
        start_time=datetime.utcnow() - timedelta(minutes=1),
        end_time=datetime.utcnow()
    )
    assert len(time_range_messages) == 3 