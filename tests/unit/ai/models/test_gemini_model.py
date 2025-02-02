import pytest
import os
from src.shared.ai.models.gemini import GeminiModel, GeminiConfig

@pytest.fixture
def gemini_config(monkeypatch):
    # 使用環境變量或測試用的 API key
    api_key = os.getenv("GOOGLE_API_KEY", "test_api_key")
    return GeminiConfig(
        name="gemini",
        api_key=api_key,
        model_name="gemini-pro",
        max_tokens=1000,
        temperature=0.7
    )

@pytest.fixture
def gemini_model(gemini_config):
    return GeminiModel(gemini_config)

@pytest.mark.asyncio
class TestGeminiModel:
    async def test_initialize(self, gemini_model):
        assert gemini_model.name == "gemini"
        assert gemini_model.client is not None
        
    @pytest.mark.asyncio
    async def test_generate(self, gemini_model):
        response = await gemini_model.generate("Hello")
        assert response is not None
        assert isinstance(response.text, str)
        
    @pytest.mark.asyncio
    async def test_generate_stream(self, gemini_model):
        messages = [{"role": "user", "content": "Hello"}]
        async for chunk in gemini_model.generate_stream(messages):
            assert isinstance(chunk, str)
            
    @pytest.mark.asyncio
    async def test_count_tokens(self, gemini_model):
        count = await gemini_model.count_tokens("Hello, world!")
        assert isinstance(count, int)
        assert count > 0 