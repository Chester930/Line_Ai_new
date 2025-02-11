import pytest
from unittest.mock import AsyncMock, patch
from src.shared.ai.models.gemini import GeminiModel
from src.shared.exceptions import ModelError, GenerationError

@pytest.mark.asyncio
class TestGeminiModelErrors:
    async def test_invalid_api_key(self):
        """測試無效的 API key"""
        with patch('google.generativeai.GenerativeModel', side_effect=Exception("Invalid API key")):
            with pytest.raises(ModelError) as exc_info:
                model = GeminiModel(api_key="invalid_key")
                await model.generate("test")
            assert "初始化失敗" in str(exc_info.value)
        
    async def test_generation_error(self, mock_gemini_model):
        """測試生成錯誤"""
        mock_gemini_model.generate = AsyncMock(side_effect=GenerationError("Generation failed"))
        
        with pytest.raises(GenerationError) as exc_info:
            await mock_gemini_model.generate("test")
        assert "Generation failed" in str(exc_info.value)
        
    async def test_stream_error(self, mock_gemini_model):
        """測試流式生成錯誤"""
        mock_gemini_model.generate_stream = AsyncMock(side_effect=GenerationError("Stream failed"))
        
        with pytest.raises(GenerationError) as exc_info:
            await mock_gemini_model.generate_stream("test")
        assert "Stream failed" in str(exc_info.value) 