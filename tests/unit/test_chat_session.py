import pytest
from unittest.mock import Mock, patch
from src.shared.chat.session import ChatSession
from src.shared.ai.base import BaseAIModel

@pytest.fixture
def mock_ai_model():
    """模擬 AI 模型"""
    model = Mock(spec=BaseAIModel)
    model.generate_response.return_value = "測試回應"
    return model

@pytest.fixture
def chat_session():
    """創建聊天會話"""
    with patch('src.shared.ai.factory.ModelFactory.create_model') as mock_create:
        mock_model = Mock(spec=BaseAIModel)
        mock_model.generate_response.return_value = "測試回應"
        mock_create.return_value = mock_model
        session = ChatSession('test_user')
        return session

def test_chat_session_initialization(chat_session):
    """測試聊天會話初始化"""
    assert chat_session.user_id == 'test_user'
    assert chat_session.current_model == 'gemini'

def test_send_message(chat_session):
    """測試發送消息"""
    response = chat_session.send_message("你好")
    assert response == "測試回應"
    chat_session.model.generate_response.assert_called_once()

def test_switch_model(chat_session):
    """測試切換模型"""
    with patch('src.shared.ai.factory.ModelFactory.create_model') as mock_create:
        mock_model = Mock(spec=BaseAIModel)
        mock_create.return_value = mock_model
        
        # 測試切換到有效模型
        assert chat_session.switch_model('gemini') is True
        
        # 測試切換到無效模型
        mock_create.side_effect = ValueError("無效模型")
        assert chat_session.switch_model('invalid_model') is False

def test_clear_context(chat_session):
    """測試清除上下文"""
    # 先添加一些消息
    chat_session.send_message("你好")
    # 清除上下文
    chat_session.clear_context()
    # 驗證上下文是否為空
    assert len(chat_session.context.get_messages()) == 0

def test_session_error_handling(chat_session):
    """測試錯誤處理"""
    # 模擬生成回應時出錯
    chat_session.model.generate_response.side_effect = Exception("測試錯誤")
    
    with pytest.raises(Exception):
        chat_session.send_message("你好")

def test_multiple_messages(chat_session):
    """測試多條消息處理"""
    responses = []
    messages = ["你好", "今天天氣如何？", "再見"]
    
    for msg in messages:
        response = chat_session.send_message(msg)
        responses.append(response)
    
    assert len(responses) == len(messages)
    assert all(response == "測試回應" for response in responses)
    assert chat_session.model.generate_response.call_count == len(messages)

def test_context_management(chat_session):
    """測試上下文管理"""
    # 發送消息並檢查上下文
    chat_session.send_message("你好")
    messages = chat_session.context.get_messages()
    
    assert len(messages) == 2  # 用戶消息和助手回應
    assert messages[0]["role"] == "user"
    assert messages[0]["content"] == "你好"
    assert messages[1]["role"] == "assistant"
    assert messages[1]["content"] == "測試回應" 