import pytest
from datetime import datetime, timedelta
from unittest.mock import Mock, patch
from src.shared.chat.session import ChatSession, Message, Context
from src.shared.ai.base import ModelType, AIResponse

@pytest.fixture
def chat_session():
    """創建測試用會話"""
    return ChatSession("test_user")

@pytest.fixture
def sample_message():
    """創建測試用消息"""
    return Message(
        content="測試消息",
        role="user",
        type="text"
    )

def test_message_creation():
    """測試消息創建"""
    message = Message(content="測試", role="user")
    assert message.content == "測試"
    assert message.role == "user"
    assert isinstance(message.timestamp, datetime)

def test_context_message_management():
    """測試上下文消息管理"""
    context = Context()
    message = Message(content="測試", role="user")
    
    context.add_message(message)
    assert len(context.messages) == 1
    assert context.messages[0] == message
    
    recent = context.get_recent_messages(limit=1)
    assert len(recent) == 1
    assert recent[0] == message

@pytest.mark.asyncio
async def test_process_message(chat_session, sample_message):
    """測試消息處理"""
    mock_response = AIResponse(
        text="測試響應",
        model=ModelType.GEMINI,
        tokens=5
    )
    
    with patch('src.shared.ai.factory.AIModelFactory.create') as mock_create:
        mock_model = Mock()
        mock_model.generate.return_value = mock_response
        mock_create.return_value = mock_model
        
        response = await chat_session.process_message(sample_message)
        
        assert response.text == "測試響應"
        assert len(chat_session.context.messages) == 2
        assert chat_session.context.messages[-1].role == "assistant"

def test_session_expiration(chat_session):
    """測試會話過期"""
    # 設置最後活動時間為一小時前
    chat_session.last_active = datetime.now() - timedelta(hours=2)
    assert chat_session.is_expired(timeout=3600)
    
    # 更新活動時間
    chat_session.last_active = datetime.now()
    assert not chat_session.is_expired(timeout=3600) 