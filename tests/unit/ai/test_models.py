import pytest
from unittest.mock import Mock, patch
from src.shared.ai.base import BaseAIModel, AIResponse, AIModelError
from src.shared.ai.factory import AIModelFactory
from src.shared.session.base import Message

class TestModel(BaseAIModel):
    """測試模型"""
    async def generate(self, messages, **kwargs):
        return AIResponse(
            content="Test response",
            model="test_model"
        )
    
    async def validate(self):
        return True

@pytest.fixture
def messages():
    """測試消息"""
    return [
        Message(role="user", content="Hello"),
        Message(role="assistant", content="Hi"),
        Message(role="user", content="How are you?")
    ]

def test_model_registration():
    """測試模型註冊"""
    # 註冊測試模型
    AIModelFactory.register_model("test", TestModel)
    
    # 驗證註冊
    assert "test" in AIModelFactory._models
    assert AIModelFactory._models["test"] == TestModel

@pytest.mark.asyncio
async def test_model_creation():
    """測試模型創建"""
    with patch("src.shared.config.manager.config_manager.get_ai_config") as mock_config:
        # 模擬配置
        mock_config.return_value = {
            "default_provider": "test",
            "test": {
                "api_key": "test_key"
            }
        }
        
        # 註冊並創建測試模型
        AIModelFactory.register_model("test", TestModel)
        model = AIModelFactory.create_model()
        
        # 驗證
        assert isinstance(model, TestModel)
        assert model.api_key == "test_key"

@pytest.mark.asyncio
async def test_model_generation(messages):
    """測試模型生成"""
    # 創建測試模型
    model = TestModel("test_key")
    
    # 生成回應
    response = await model.generate(messages)
    
    # 驗證
    assert isinstance(response, AIResponse)
    assert response.content == "Test response"
    assert response.model == "test_model"

def test_message_formatting(messages):
    """測試消息格式化"""
    model = TestModel("test_key")
    formatted = model._format_messages(messages)
    
    # 驗證格式
    assert len(formatted) == len(messages)
    assert all(
        "role" in msg and "content" in msg
        for msg in formatted
    )

@pytest.mark.asyncio
async def test_error_handling():
    """測試錯誤處理"""
    model = TestModel("test_key")
    
    # 觸發錯誤
    with pytest.raises(AIModelError):
        model._handle_error(
            Exception("Test error"),
            "Test operation"
        ) 