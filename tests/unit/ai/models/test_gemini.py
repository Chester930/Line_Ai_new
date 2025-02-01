import pytest
from unittest.mock import Mock, patch, AsyncMock
from src.shared.ai.models.gemini import GeminiModel, GeminiConfig
from src.shared.ai.base import ModelResponse, Message
from src.shared.exceptions import ModelError

class TestGeminiModel:
    @pytest.fixture
    def config(self):
        return GeminiConfig(
            name="gemini",
            api_key="test_key",
            model_name="gemini-pro",
            max_tokens=1000,
            temperature=0.7
        )
    
    @pytest.fixture
    async def model(self, config):
        model = GeminiModel(config)
        yield model
        # 清理資源
        if hasattr(model, 'client'):
            await model.client.close()
    
    @pytest.mark.asyncio
    @patch('google.generativeai.GenerativeModel')
    async def test_initialize(self, mock_genai, model):
        """測試模型初始化"""
        assert model.name == "gemini"
        assert model.config.api_key == "test_key"
        assert model.config.model_name == "gemini-pro"
    
    @pytest.mark.asyncio
    @patch('google.generativeai.GenerativeModel')
    async def test_generate_success(self, mock_genai, model):
        """測試成功生成回應"""
        # 設置模擬回應
        mock_response = Mock()
        mock_response.text = "Test response"
        mock_response.prompt_feedback.safety_ratings = []
        mock_response.candidates = [
            Mock(token_count=20)
        ]
        mock_response.prompt_token_count = 10
        
        mock_model = mock_genai.return_value
        mock_model.generate_content.return_value = mock_response
        
        # 執行生成
        result = await model.generate("Test prompt")
        
        # 驗證結果
        assert isinstance(result, ModelResponse)
        assert result.text == "Test response"
        assert result.usage["total_tokens"] == 30
        assert result.model_info["model"] == "gemini-pro"
    
    @pytest.mark.asyncio
    @patch('google.generativeai.GenerativeModel')
    async def test_generate_with_context(self, mock_genai, model):
        """測試帶上下文生成"""
        # 設置模擬回應
        mock_response = Mock()
        mock_response.text = "Test response"
        mock_response.prompt_feedback.safety_ratings = []
        mock_response.candidates = [
            Mock(token_count=25)
        ]
        mock_response.prompt_token_count = 15
        
        mock_model = mock_genai.return_value
        mock_model.generate_content.return_value = mock_response
        
        # 準備上下文
        context = [
            {"role": "user", "content": "Previous message"},
            {"role": "assistant", "content": "Previous response"}
        ]
        
        # 執行生成
        result = await model.generate("Test prompt", context=context)
        
        # 驗證結果
        assert isinstance(result, ModelResponse)
        assert result.text == "Test response"
        assert result.usage["total_tokens"] == 40
    
    @pytest.mark.asyncio
    @patch('google.generativeai.GenerativeModel')
    async def test_generate_stream(self, mock_genai, model):
        """測試流式生成"""
        # 設置模擬回應
        mock_chunks = [
            Mock(text="Hello"),
            Mock(text=" world"),
            Mock(text="!")
        ]
        
        mock_model = mock_genai.return_value
        mock_model.generate_content.return_value = mock_chunks
        
        # 準備消息
        messages = [
            Message.create(user_id="test", content="Hi", role="user")
        ]
        
        # 執行流式生成
        chunks = []
        async for chunk in model.generate_stream(messages):
            chunks.append(chunk)
        
        # 驗證結果
        assert len(chunks) == 3
        assert "".join(chunks) == "Hello world!"
    
    @pytest.mark.asyncio
    @patch('google.generativeai.GenerativeModel')
    async def test_count_tokens(self, mock_genai, model):
        """測試計算 tokens"""
        mock_model = mock_genai.return_value
        mock_model.count_tokens.return_value = Mock(total_tokens=5)
        
        count = await model.count_tokens("Hello, world!")
        assert count == 5
    
    @pytest.mark.asyncio
    @patch('google.generativeai.GenerativeModel')
    async def test_error_handling(self, mock_genai, model):
        """測試錯誤處理"""
        mock_model = mock_genai.return_value
        mock_model.generate_content.side_effect = Exception("Test error")
        
        with pytest.raises(ModelError) as exc_info:
            await model.generate("Test prompt")
        
        assert "Failed to generate response" in str(exc_info.value)
    
    @pytest.mark.asyncio
    @patch('google.generativeai.GenerativeModel')
    async def test_validate(self, mock_genai, model):
        """測試模型驗證"""
        mock_model = mock_genai.return_value
        mock_model.generate_content.return_value = Mock(text="Test")
        
        is_valid = await model.validate()
        assert is_valid is True
        
        # 測試驗證失敗
        mock_model.generate_content.side_effect = Exception("Test error")
        is_valid = await model.validate()
        assert is_valid is False 