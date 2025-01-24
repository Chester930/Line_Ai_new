import pytest
from src.shared.ai.factory import AIModelFactory
from src.shared.ai.base import ModelType, BaseAIModel, AIResponse

class MockModel(BaseAIModel):
    """模擬模型類"""
    async def generate(self, prompt, context=None, **kwargs):
        return AIResponse(text="mock", model=ModelType.GEMINI, tokens=1)
    
    async def analyze_image(self, image, prompt=None):
        return AIResponse(text="mock", model=ModelType.GEMINI, tokens=1)
    
    async def validate_response(self, response):
        return True

@pytest.fixture
def register_mock_model():
    """註冊模擬模型"""
    AIModelFactory._models.clear()
    AIModelFactory.register(ModelType.GEMINI)(MockModel)

@pytest.mark.asyncio
async def test_model_creation(register_mock_model):
    """測試模型創建"""
    model = await AIModelFactory.create(ModelType.GEMINI)
    assert isinstance(model, MockModel)

@pytest.mark.asyncio
async def test_invalid_model_type():
    """測試無效模型類型"""
    with pytest.raises(ValueError):
        await AIModelFactory.create(ModelType.GPT) 