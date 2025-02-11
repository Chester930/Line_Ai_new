import pytest
from unittest.mock import Mock, patch
from src.shared.chat.session import ChatSession
from src.shared.chat.context import Context, ContextManager
from src.shared.ai.base import BaseAIModel

@pytest.fixture
def mock_ai_model():
    model = Mock(spec=BaseAIModel)
    model.generate_response.return_value = "Test response"
    return model

@pytest.fixture
def chat_session(mock_ai_model):
    with patch('src.shared.ai.factory.ModelFactory.create_model', return_value=mock_ai_model):
        session = ChatSession('test_user')
        return session

def test_chat_session(chat_session, mock_ai_model):
    """測試聊天會話"""
    assert chat_session.user_id == 'test_user'
    assert chat_session.current_model == 'gemini'
    
    # 測試發送消息
    response = chat_session.send_message("Hello")
    assert response == "Test response"
    mock_ai_model.generate_response.assert_called_once()

def test_context():
    """測試上下文管理"""
    context = Context()
    context.add_message("user", "Hello")
    context.add_message("assistant", "Hi")
    
    messages = context.get_messages()
    assert len(messages) == 2
    assert messages[0]["role"] == "user"
    assert messages[1]["role"] == "assistant"

def test_session_manager():
    """測試會話管理器"""
    manager = ContextManager()
    context = manager.get_or_create_context("test_user")
    
    assert context is not None
    assert manager.get_or_create_context("test_user") is context 