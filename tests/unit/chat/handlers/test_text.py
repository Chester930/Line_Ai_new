import pytest
from unittest.mock import patch, Mock
from src.shared.chat.handlers.text import TextMessageHandler
from src.shared.chat.session import Message
from src.shared.ai.base import AIResponse, ModelType

@pytest.fixture
def text_handler():
    return TextMessageHandler()

@pytest.fixture
def text_message():
    return Message(
        content="hello",
        role="user",
        type="text"
    )

@pytest.mark.asyncio
async def test_text_validation(text_handler, text_message):
    """測試文本驗證"""
    assert await text_handler.validate(text_message)
    
    # 測試空消息
    empty_message = Message(content="", role="user", type="text")
    assert not await text_handler.validate(empty_message)
    
    # 測試錯誤類型
    wrong_type = Message(content="test", role="user", type="image")
    assert not await text_handler.validate(wrong_type)

@pytest.mark.asyncio
async def test_text_processing(text_handler, text_message):
    """測試文本處理"""
    mock_response = AIResponse(
        text="response",
        model=ModelType.GEMINI,
        tokens=5
    )
    
    with patch('src.shared.ai.factory.AIModelFactory.create') as mock_create:
        mock_model = Mock()
        mock_model.generate.return_value = mock_response
        mock_create.return_value = mock_model
        
        result = await text_handler.handle(text_message)
        
        assert result["success"]
        assert result["response"] == "response"
        assert result["model"] == "gemini"
        assert result["tokens"] == 5 