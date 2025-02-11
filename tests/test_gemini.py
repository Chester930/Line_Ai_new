import pytest
from unittest.mock import AsyncMock, patch
from src.shared.ai.models.gemini import GeminiModel
from src.shared.config.base import ConfigManager

class TestGemini:
    @pytest.fixture
    def config(self):
        """配置測試夾具"""
        config = ConfigManager()
        config.set("GOOGLE_API_KEY", "test_api_key")
        return config
        
    @pytest.fixture
    def model(self, config):
        """模型測試夾具"""
        return GeminiModel(config)

    @pytest.mark.asyncio
    async def test_model_initialization(self, model, config):
        """測試模型初始化"""
        assert model.api_key == "test_api_key"
        assert model.model_name == "gemini-pro"
        
    @pytest.mark.asyncio
    async def test_text_generation(self, model):
        """測試文本生成"""
        with patch('google.generativeai.GenerativeModel.generate_content', new_callable=AsyncMock) as mock_generate:
            mock_generate.return_value.text = "Test response"
            response = await model.generate_text("Test prompt", max_tokens=100)
            assert isinstance(response, str)
            assert len(response) > 0
        
    @pytest.mark.asyncio
    async def test_streaming_response(self, model):
        """測試流式響應"""
        async def mock_stream():
            yield "Part 1"
            yield "Part 2"
            
        with patch('google.generativeai.GenerativeModel.generate_content', new_callable=AsyncMock) as mock_generate:
            mock_generate.return_value.text_stream = mock_stream
            chunks = []
            async for chunk in model.generate_stream("Test prompt"):
                chunks.append(chunk)
                
            assert len(chunks) == 2
            assert all(isinstance(c, str) for c in chunks)

    @pytest.mark.asyncio
    async def test_gemini_streaming(self, model):
        """測試串流生成"""
        with patch('google.generativeai.GenerativeModel.generate_content', new_callable=AsyncMock) as mock_generate:
            mock_generate.return_value.text = "Test response"
            mock_generate.return_value.chunks = [
                AsyncMock(text="Part 1"),
                AsyncMock(text="Part 2")
            ]
            
            # 測試普通生成
            response = await model.generate_text("Test prompt")
            assert response == "Test response"
            
            # 測試串流生成
            chunks = []
            async for chunk in model.generate_stream("Test prompt"):
                chunks.append(chunk)
                
            assert len(chunks) == 2
            assert chunks == ["Part 1", "Part 2"] 