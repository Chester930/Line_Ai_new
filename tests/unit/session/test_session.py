import pytest
from datetime import datetime, timedelta
from src.shared.session.base import Message, Session
from src.shared.session.memory import MemorySessionManager
from src.shared.session.factory import SessionManagerFactory

@pytest.fixture
def message():
    """測試消息"""
    return Message(
        role="user",
        content="Hello, World!"
    )

@pytest.fixture
def session():
    """測試會話"""
    return Session(
        user_id="test_user",
        metadata={"test": "value"}
    )

@pytest.fixture
def session_manager():
    """會話管理器"""
    return MemorySessionManager()

def test_message_creation(message):
    """測試消息創建"""
    assert message.role == "user"
    assert message.content == "Hello, World!"
    assert message.message_id is not None
    assert isinstance(message.timestamp, datetime)

def test_session_creation(session):
    """測試會話創建"""
    assert session.session_id is not None
    assert session.user_id == "test_user"
    assert session.metadata == {"test": "value"}
    assert isinstance(session.created_at, datetime)
    assert isinstance(session.updated_at, datetime)

def test_session_messages(session, message):
    """測試會話消息操作"""
    # 添加消息
    session.add_message(message)
    assert len(session.messages) == 1
    assert session.messages[0] == message
    
    # 清空消息
    session.clear_messages()
    assert len(session.messages) == 0

def test_session_message_filtering(session):
    """測試消息過濾"""
    # 添加測試消息
    now = datetime.now()
    messages = [
        Message(
            role="user",
            content=f"Message {i}",
            timestamp=now + timedelta(minutes=i)
        )
        for i in range(5)
    ]
    for msg in messages:
        session.add_message(msg)
    
    # 測試限制
    filtered = session.get_messages(limit=3)
    assert len(filtered) == 3
    assert filtered[-1] == messages[-1]
    
    # 測試時間過濾
    cutoff = now + timedelta(minutes=2)
    filtered = session.get_messages(before=cutoff)
    assert len(filtered) == 3

@pytest.mark.asyncio
async def test_session_manager(session_manager):
    """測試會話管理器"""
    # 創建會話
    session = await session_manager.create_session(
        "test_user",
        {"test": "value"}
    )
    assert session.user_id == "test_user"
    
    # 保存會話
    assert await session_manager.save_session(session)
    
    # 獲取會話
    loaded = await session_manager.get_session(session.session_id)
    assert loaded is not None
    assert loaded.session_id == session.session_id
    
    # 列出會話
    sessions = await session_manager.list_sessions()
    assert len(sessions) == 1
    assert sessions[0].session_id == session.session_id
    
    # 按用戶過濾
    sessions = await session_manager.list_sessions("test_user")
    assert len(sessions) == 1
    sessions = await session_manager.list_sessions("other_user")
    assert len(sessions) == 0
    
    # 刪除會話
    assert await session_manager.delete_session(session.session_id)
    assert await session_manager.get_session(session.session_id) is None

def test_session_manager_factory():
    """測試會話管理器工廠"""
    # 創建默認管理器
    manager = SessionManagerFactory.create_manager()
    assert isinstance(manager, MemorySessionManager)
    
    # 創建指定類型
    manager = SessionManagerFactory.create_manager("memory")
    assert isinstance(manager, MemorySessionManager)
    
    # 測試無效類型
    manager = SessionManagerFactory.create_manager("invalid")
    assert isinstance(manager, MemorySessionManager) 