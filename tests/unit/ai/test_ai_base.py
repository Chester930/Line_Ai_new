import pytest
from src.shared.ai.base import ModelType, AIResponse, BaseAIModel, AIModel
from src.shared.utils.types import Optional, Callable

def test_model_type_enum():
    """測試模型類型枚舉"""
    assert ModelType.GEMINI.value == "gemini"
    assert ModelType.GPT.value == "gpt"
    assert ModelType.CLAUDE.value == "claude"

def test_ai_response_creation():
    """測試 AI 響應數據類"""
    response = AIResponse(
        text="測試響應",
        model=ModelType.GEMINI,
        tokens=10,
        raw_response={"raw": "data"},
        error=None
    )
    
    assert response.text == "測試響應"
    assert response.model == ModelType.GEMINI
    assert response.tokens == 10
    assert response.raw_response == {"raw": "data"}
    assert response.error is None

class TestModel(BaseAIModel):
    """測試用模型類"""
    async def generate(self, prompt, context=None, **kwargs):
        return AIResponse(text="test", model=ModelType.GEMINI, tokens=1)
    
    async def analyze_image(self, image, prompt=None):
        return AIResponse(text="test", model=ModelType.GEMINI, tokens=1)
    
    async def validate_response(self, response):
        return True

@pytest.mark.asyncio
async def test_base_model_error_handling():
    """測試基礎模型錯誤處理"""
    model = TestModel()
    error = Exception("測試錯誤")
    response = await model.handle_error(error)
    
    assert response.error == "測試錯誤"
    assert response.text == ""
    assert response.tokens == 0 