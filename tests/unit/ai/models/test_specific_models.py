import pytest
from unittest.mock import Mock, patch
from src.shared.ai.models.gemini import GeminiModel
from src.shared.ai.models.gpt import GPTModel
from src.shared.ai.models.claude import ClaudeModel
from src.shared.session.base import Message

@pytest.fixture
def messages():
    """測試消息"""
    return [
        Message(role="user", content="Hello"),
        Message(role="assistant", content="Hi"),
        Message(role="user", content="How are you?")
    ]

@pytest.mark.asyncio
async def test_gemini_model(messages):
    """測試 Gemini 模型"""
    with patch("google.generativeai.GenerativeModel") as mock_model:
        # 模擬回應
        mock_chat = Mock()
        mock_chat.send_message.return_value = Mock(
            text="I'm doing great!"
        )
        mock_model.return_value.start_chat.return_value = mock_chat
        
        # 創建模型
        model = GeminiModel("test_key")
        response = await model.generate(messages)
        
        # 驗證
        assert response.content == "I'm doing great!"
        assert response.model == "gemini-pro"

@pytest.mark.asyncio
async def test_gpt_model(messages):
    """測試 GPT 模型"""
    with patch("openai.ChatCompletion.acreate") as mock_create:
        # 模擬回應
        mock_response = Mock()
        mock_response.choices = [
            Mock(message=Mock(content="I'm fine!"))
        ]
        mock_response.usage = {"total_tokens": 10}
        mock_create.return_value = mock_response
        
        # 創建模型
        model = GPTModel("test_key")
        response = await model.generate(messages)
        
        # 驗證
        assert response.content == "I'm fine!"
        assert response.model == "gpt-3.5-turbo"
        assert response.usage == {"total_tokens": 10}

@pytest.mark.asyncio
async def test_claude_model(messages):
    """測試 Claude 模型"""
    with patch("anthropic.Anthropic") as mock_anthropic:
        # 模擬回應
        mock_client = Mock()
        mock_response = Mock()
        mock_response.content = [Mock(text="Doing well!")]
        mock_response.usage = {"prompt_tokens": 10}
        mock_client.messages.create.return_value = mock_response
        mock_anthropic.return_value = mock_client
        
        # 創建模型
        model = ClaudeModel("test_key")
        response = await model.generate(messages)
        
        # 驗證
        assert response.content == "Doing well!"
        assert response.model == "claude-3-sonnet"
        assert response.usage == {"prompt_tokens": 10}

@pytest.mark.asyncio
async def test_model_validation():
    """測試模型驗證"""
    # Gemini 驗證
    with patch("google.generativeai.GenerativeModel") as mock_gemini:
        mock_gemini.return_value.generate_content.return_value = Mock(
            text="Test"
        )
        model = GeminiModel("test_key")
        assert await model.validate()
    
    # GPT 驗證
    with patch("openai.Model.aretrieve") as mock_gpt:
        mock_gpt.return_value = True
        model = GPTModel("test_key")
        assert await model.validate()
    
    # Claude 驗證
    with patch("anthropic.Anthropic") as mock_anthropic:
        mock_client = Mock()
        mock_response = Mock(content=[Mock(text="Test")])
        mock_client.messages.create.return_value = mock_response
        mock_anthropic.return_value = mock_client
        model = ClaudeModel("test_key")
        assert await model.validate() 