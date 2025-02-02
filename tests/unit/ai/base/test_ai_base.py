import pytest
from src.shared.ai.base import BaseAIModel, ModelResponse, Message
from src.shared.session.base import AIResponse

class TestBaseAIModel:
    @pytest.fixture
    def base_model(self):
        class TestModel(BaseAIModel):
            async def generate(self, *args, **kwargs):
                raise NotImplementedError()
                
            async def generate_stream(self, *args, **kwargs):
                raise NotImplementedError()
                
            async def count_tokens(self, *args, **kwargs):
                raise NotImplementedError()
                
            async def validate(self, *args, **kwargs):
                raise NotImplementedError()
            
            async def validate_response(self, response: dict) -> bool:
                return bool(response and response.get("text"))
            
            async def handle_error(self, error: Exception) -> AIResponse:
                return AIResponse(
                    text="錯誤：" + str(error),
                    model="test",
                    tokens=0,
                    raw_response={"error": str(error)}
                )
        
        return TestModel("test_key")
    
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

    @pytest.mark.asyncio
    async def test_message_handling(self, base_model):
        """測試消息處理"""
        messages = [
            Message(
                id=1,
                role="user",
                content="test message",
                user_id="test_user",
                type="text"
            )
        ]
        
        # 測試消息格式化
        formatted = base_model._format_messages(messages)
        assert len(formatted) == 1
        assert formatted[0]["role"] == "user"
        assert formatted[0]["content"] == "test message"

    @pytest.mark.asyncio
    async def test_response_validation(self, base_model):
        """測試響應驗證"""
        # 測試有效響應
        valid_response = {
            "text": "test response",
            "model": "test_model",
            "tokens": 10
        }
        assert await base_model.validate_response(valid_response)
        
        # 測試無效響應
        invalid_responses = [
            {},  # 空響應
            {"text": ""},  # 空文本
            {"model": "test"},  # 缺少文本
            None  # None 值
        ]
        for resp in invalid_responses:
            assert not await base_model.validate_response(resp)

    @pytest.mark.asyncio
    async def test_error_handling_variations(self, base_model):
        """測試不同類型的錯誤處理"""
        # 測試一般異常
        error = Exception("一般錯誤")
        response = await base_model.handle_error(error)
        assert "一般錯誤" in response.text
        
        # 測試特定異常
        error = ValueError("無效的值")
        response = await base_model.handle_error(error)
        assert "無效的值" in response.text
        
        # 測試空異常
        error = Exception()
        response = await base_model.handle_error(error)
        assert response.text
        assert response.tokens == 0

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
    
    def test_response_validation(self):
        """測試響應驗證"""
        # 測試有效響應
        response = ModelResponse(
            text="test",
            usage={"total_tokens": 5},
            model_info={"model": "test"}
        )
        assert response.text == "test"
        assert response.usage["total_tokens"] == 5
        
        # 測試最小化參數
        response = ModelResponse(
            text="test",
            usage={},  # 提供空字典作為必需參數
            model_info={}  # 提供空字典作為必需參數
        )
        assert response.text == "test"
        assert response.usage == {}
        assert response.model_info == {} 