import pytest
from src.shared.ai.factory import AIModelFactory, ModelType
from src.shared.ai.models.gemini import GeminiModel

@pytest.mark.asyncio
async def test_create_gemini():
    """測試創建 Gemini 模型"""
    model = await AIModelFactory.create(ModelType.GEMINI)
    assert isinstance(model, GeminiModel)

@pytest.mark.asyncio
async def test_create_unsupported():
    """測試創建不支持的模型"""
    with pytest.raises(ValueError, match="不支持的模型類型"):
        await AIModelFactory.create(ModelType.GPT) 