import pytest
from src.shared.ai.base import BaseAIModel, ModelResponse, Message

class TestBaseAIModel:
    @pytest.fixture
    def base_model(self):
        return BaseAIModel("test_key")
    
    def test_initialization(self, base_model):
        assert base_model.api_key == "test_key"
    
    @pytest.mark.asyncio
    async def test_abstract_methods(self, base_model):
        with pytest.raises(NotImplementedError):
            await base_model.generate("test")
            
        with pytest.raises(NotImplementedError):
            await base_model.generate_stream([])
            
        with pytest.raises(NotImplementedError):
            await base_model.count_tokens("test")
            
        with pytest.raises(NotImplementedError):
            await base_model.validate()

    @pytest.mark.asyncio
    async def test_base_model_validation(self, base_model):
        """測試基礎模型驗證"""
        # 驗證響應
        valid_response = {"text": "test"}
        assert await base_model.validate_response(valid_response)
        
        # 驗證無效響應
        invalid_response = {}
        assert not await base_model.validate_response(invalid_response)

    @pytest.mark.asyncio
    async def test_base_model_error_handling(self, base_model):
        """測試錯誤處理"""
        error = Exception("Test error")
        response = await base_model.handle_error(error)
        
        assert "error" in response.raw_response
        assert response.tokens == 0
        assert "錯誤" in response.text

class TestModelResponse:
    def test_response_creation(self):
        response = ModelResponse(
            text="test response",
            usage={"total_tokens": 10},
            model_info={"model": "test"}
        )
        assert response.text == "test response"
        assert response.usage["total_tokens"] == 10
        assert response.model_info["model"] == "test" 