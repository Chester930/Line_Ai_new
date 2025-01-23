import pytest
from unittest.mock import Mock, patch
from src.shared.ai.factory import ModelFactory
from src.shared.ai.base import BaseAIModel
from src.shared.ai.models.gemini import GeminiModel
from src.shared.config.config import config

@pytest.fixture
def model_factory():
    return ModelFactory()

@pytest.fixture
def gemini_model():
    """創建一個模擬的 Gemini 模型"""
    with patch('src.shared.ai.models.gemini.GeminiModel._initialize'):
        model = GeminiModel()
        # 手動設置 model 屬性
        mock_genai_model = Mock()
        mock_genai_model.generate_content.return_value = Mock(text="測試回應")
        model.model = mock_genai_model
        return model

def test_model_factory(model_factory):
    """測試 AI 模型工廠"""
    with patch('src.shared.ai.models.gemini.GeminiModel._initialize'):
        model = model_factory.create_model('gemini')
        assert model.model_type == 'gemini'

def test_invalid_model_type(model_factory):
    """測試無效的模型類型"""
    with pytest.raises(ValueError):
        model_factory.create_model('invalid_model')

def test_model_initialization_failure(model_factory):
    """測試模型初始化失敗"""
    with patch('src.shared.ai.models.gemini.GeminiModel._initialize', 
              side_effect=Exception('Init failed')):
        with pytest.raises(Exception):
            model_factory.create_model('gemini')

def test_available_models(model_factory):
    """測試獲取可用模型列表"""
    models = model_factory.get_available_models()
    assert 'gemini' in models
    assert len(models) == 1

def test_register_model(model_factory):
    """測試註冊新模型"""
    class TestModel(BaseAIModel):
        def _initialize(self):
            pass
        def generate_response(self, messages):
            return "test response"
    
    ModelFactory.register_model('test', TestModel)
    assert 'test' in model_factory.get_available_models()
    ModelFactory._models.pop('test', None)

def test_gemini_model_methods(gemini_model):
    """測試 Gemini 模型的方法"""
    # 測試驗證回應
    assert gemini_model.validate_response("有效回應") is True
    assert gemini_model.validate_response("") is False
    assert gemini_model.validate_response(None) is False

    # 測試格式化消息
    messages = [
        {"role": "user", "content": "你好"},
        {"role": "assistant", "content": "你好！"},
        {"invalid": "message"}  # 應該被過濾掉
    ]
    formatted = gemini_model.format_messages(messages)
    assert len(formatted) == 2
    assert all(key in formatted[0] for key in ["role", "content"])

    # 測試錯誤處理
    error_response = gemini_model.handle_error(Exception("測試錯誤"))
    assert "抱歉" in error_response

    # 測試模型信息
    info = gemini_model.model_info
    assert info["type"] == "gemini"
    assert "temperature" in info
    assert "max_tokens" in info
    assert "top_p" in info

def test_model_settings_update(gemini_model):
    """測試更新模型設置"""
    settings = {
        "temperature": 0.8,
        "max_tokens": 2000,
        "top_p": 0.95
    }
    gemini_model.update_settings(settings)
    
    assert gemini_model.temperature == 0.8
    assert gemini_model.max_tokens == 2000
    assert gemini_model.top_p == 0.95

def test_gemini_response_generation(gemini_model):
    """測試 Gemini 回應生成"""
    response = gemini_model.generate_response([
        {"role": "user", "content": "你好"}
    ])
    
    assert response == "測試回應"
    gemini_model.model.generate_content.assert_called_once() 