import pytest
from datetime import datetime, timedelta
from src.shared.chat.manager import ChatManager
from src.shared.chat.session import ChatSession

@pytest.fixture
def chat_manager():
    return ChatManager()

@pytest.mark.asyncio
async def test_session_creation(chat_manager):
    """測試會話創建"""
    session = await chat_manager.get_or_create_session("user1")
    assert isinstance(session, ChatSession)
    assert session.user_id == "user1"
    assert "user1" in chat_manager.sessions

@pytest.mark.asyncio
async def test_session_reuse(chat_manager):
    """測試會話重用"""
    session1 = await chat_manager.get_or_create_session("user1")
    session2 = await chat_manager.get_or_create_session("user1")
    assert session1 is session2

@pytest.mark.asyncio
async def test_message_processing(chat_manager):
    """測試消息處理"""
    result = await chat_manager.process_message(
        user_id="user1",
        message_type="text",
        content="你好",
        metadata={"importance": 0.8}
    )
    
    assert result["success"]
    assert "response" in result

@pytest.mark.asyncio
async def test_session_cleanup(chat_manager):
    """測試會話清理"""
    # 創建過期會話
    session = await chat_manager.get_or_create_session("user1")
    session.last_active = datetime.now() - timedelta(hours=2)
    
    await chat_manager.cleanup_sessions()
    assert "user1" not in chat_manager.sessions

@pytest.mark.asyncio
async def test_invalid_message_type(chat_manager):
    """測試無效消息類型"""
    result = await chat_manager.process_message(
        user_id="user1",
        message_type="invalid",
        content="test"
    )
    
    assert not result["success"]
    assert "error" in result 