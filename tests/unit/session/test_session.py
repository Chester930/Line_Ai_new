import pytest
from datetime import datetime, timedelta
from src.shared.session.base import Message, Session
from src.shared.session.memory import MemorySessionManager  # 確保這一行正確
from uuid import UUID

@pytest.fixture
def message():
    """測試消息的 fixture"""
    return Message(
        user_id="test_user",
        content="Hello, World!"
    )

@pytest.fixture
def session():
    """測試會話的 fixture"""
    return Session(
        session_id="test_session",
        user_id="test_user",
        metadata={"test": "value"}
    )

def test_message_creation():
    """測試消息創建"""
    message = Message(
        user_id="test_user",
        content="Hello, World!",
        message_type="text"
    )
    
    assert isinstance(message.id, UUID)
    assert message.user_id == "test_user"
    assert message.content == "Hello, World!"
    assert message.type == "text"
    assert isinstance(message.timestamp, datetime)
    assert isinstance(message.metadata, dict)

def test_session_creation():
    """測試會話創建"""
    session = Session(
        session_id="test_session",
        user_id="test_user",
        ttl=3600
    )
    
    assert session.id == "test_session"
    assert session.user_id == "test_user"
    assert session.ttl == 3600
    assert isinstance(session.created_at, datetime)
    assert isinstance(session.last_activity, datetime)
    assert isinstance(session.messages, list)
    assert len(session.messages) == 0

def test_session_message_management():
    """測試會話消息管理"""
    session = Session("test_session", "test_user")
    message = Message("test_user", "Test message")
    
    session.add_message(message)
    assert len(session.messages) == 1
    assert session.messages[0].content == "Test message"

def test_session_expiration():
    """測試會話過期"""
    session = Session("test_session", "test_user", ttl=1)
    assert not session.is_expired()
    
    # 模擬時間流逝
    session.last_activity = datetime.utcnow() - timedelta(seconds=2)
    assert session.is_expired()

def test_session_to_dict():
    """測試會話序列化"""
    session = Session("test_session", "test_user")
    message = Message("test_user", "Test message")
    session.add_message(message)
    
    session_dict = session.to_dict()
    assert isinstance(session_dict, dict)
    assert session_dict["id"] == "test_session"
    assert session_dict["user_id"] == "test_user"
    assert len(session_dict["messages"]) == 1
    assert session_dict["messages"][0]["content"] == "Test message"

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
    for i in range(5):
        session.add_message(Message(user_id="test_user", content=f"Message {i}"))
    
    # 測試限制
    filtered = session.get_messages(limit=3)
    assert len(filtered) == 3
    assert filtered[-1].content == "Message 4"

@pytest.mark.asyncio
async def test_session_manager():
    """測試會話管理器"""
    session_manager = MemorySessionManager()  # 確保這一行能正確執行
    
    # 創建會話
    session = await session_manager.create_session("test_user", {"test": "value"})
    assert session.user_id == "test_user"
    
    # 保存會話
    assert await session_manager.save_session(session)
    
    # 獲取會話
    loaded = await session_manager.get_session(session.id)
    assert loaded is not None
    assert loaded.id == session.id
    
    # 列出會話
    sessions = await session_manager.list_sessions()
    assert len(sessions) == 1
    assert sessions[0].id == session.id
    
    # 按用戶過濾
    user_sessions = await session_manager.list_sessions("test_user")
    assert len(user_sessions) == 1
    assert user_sessions[0].id == session.id
    
    # 刪除會話
    assert await session_manager.delete_session(session.id)
    assert await session_manager.get_session(session.id) is None