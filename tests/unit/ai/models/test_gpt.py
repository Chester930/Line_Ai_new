import pytest
from unittest.mock import Mock, patch, AsyncMock
from src.shared.ai.models.gpt import GPTModel, GPTConfig
from src.shared.ai.base import ModelResponse, Message
from src.shared.exceptions import ModelError

class TestGPTModel:
    @pytest.fixture
    def config(self):
        return GPTConfig(
            name="gpt",
            api_key="test_key",
            model_name="gpt-4",
            max_tokens=1000,
            temperature=0.7,
            organization="test-org",
            request_timeout=30
        )
    
    @pytest.fixture
    async def model(self, config):
        with patch('openai.AsyncOpenAI') as mock_openai:
            model = GPTModel(config)
            yield model
            # 清理資源
            await model.client.close()
    
    @pytest.mark.asyncio
    async def test_initialize(self, model):
        """測試模型初始化"""
        assert model.name == "gpt"
        assert model.config.api_key == "test_key"
        assert model.config.model_name == "gpt-4"
        assert model.config.organization == "test-org"
    
    @pytest.mark.asyncio
    async def test_generate_success(self, model):
        """測試成功生成回應"""
        # 設置模擬回應
        mock_response = Mock()
        mock_response.choices = [
            Mock(
                message=Mock(content="Test response"),
                finish_reason="stop"
            )
        ]
        mock_response.usage = {
            "prompt_tokens": 10,
            "completion_tokens": 20,
            "total_tokens": 30
        }
        
        # 設置模擬客戶端
        model.client.chat.completions.create = AsyncMock(
            return_value=mock_response
        )
        
        # 執行生成
        result = await model.generate("Test prompt")
        
        # 驗證結果
        assert isinstance(result, ModelResponse)
        assert result.text == "Test response"
        assert result.usage["total_tokens"] == 30
        assert result.model_info["model"] == "gpt-4"
        assert result.model_info["finish_reason"] == "stop"
    
    @pytest.mark.asyncio
    async def test_generate_with_context(self, model):
        """測試帶上下文生成"""
        # 設置模擬回應
        mock_response = Mock()
        mock_response.choices = [
            Mock(
                message=Mock(content="Test response"),
                finish_reason="stop"
            )
        ]
        mock_response.usage = {
            "prompt_tokens": 15,
            "completion_tokens": 25,
            "total_tokens": 40
        }
        
        # 設置模擬客戶端
        model.client.chat.completions.create = AsyncMock(
            return_value=mock_response
        )
        
        # 準備上下文
        context = [
            {"role": "user", "content": "Previous message"},
            {"role": "assistant", "content": "Previous response"}
        ]
        
        # 執行生成
        result = await model.generate("Test prompt", context=context)
        
        # 驗證結果
        assert isinstance(result, ModelResponse)
        assert result.text == "Test response"
        assert result.usage["total_tokens"] == 40
        
        # 驗證上下文處理
        create_args = model.client.chat.completions.create.call_args[1]
        assert len(create_args["messages"]) == 3
    
    @pytest.mark.asyncio
    async def test_generate_stream(self, model):
        """測試流式生成"""
        # 設置模擬流式回應
        mock_chunks = [
            Mock(choices=[Mock(delta=Mock(content="Hello"))]),
            Mock(choices=[Mock(delta=Mock(content=" world"))]),
            Mock(choices=[Mock(delta=Mock(content="!"))])
        ]
        
        # 設置模擬客戶端
        model.client.chat.completions.create = AsyncMock(return_value=mock_chunks)
        
        # 準備消息
        messages = [
            Message.create(user_id="test", content="Hi", role="user")
        ]
        
        # 執行流式生成
        chunks = []
        async for chunk in model.generate_stream(messages):
            chunks.append(chunk)
        
        # 驗證結果
        assert len(chunks) == 3
        assert "".join(chunks) == "Hello world!"
    
    @pytest.mark.asyncio
    async def test_count_tokens(self, model):
        """測試計算 tokens"""
        # 設置模擬 tiktoken
        with patch('tiktoken.encoding_for_model') as mock_encoding:
            mock_encoding.return_value.encode.return_value = [1, 2, 3, 4, 5]
            
            count = await model.count_tokens("Hello, world!")
            assert count == 5
    
    @pytest.mark.asyncio
    async def test_error_handling(self, model):
        """測試錯誤處理"""
        # 設置模擬錯誤
        model.client.chat.completions.create = AsyncMock(
            side_effect=Exception("Test error")
        )
        
        with pytest.raises(ModelError) as exc_info:
            await model.generate("Test prompt")
        
        assert "Failed to generate response" in str(exc_info.value)
    
    @pytest.mark.asyncio
    async def test_validate(self, model):
        """測試模型驗證"""
        # 設置模擬成功回應
        mock_response = Mock()
        mock_response.choices = [
            Mock(message=Mock(content="Test"))
        ]
        model.client.chat.completions.create = AsyncMock(
            return_value=mock_response
        )
        
        is_valid = await model.validate()
        assert is_valid is True
        
        # 測試驗證失敗
        model.client.chat.completions.create = AsyncMock(
            side_effect=Exception("Test error")
        )
        is_valid = await model.validate()
        assert is_valid is False
    
    @pytest.mark.asyncio
    async def test_timeout_handling(self, model):
        """測試超時處理"""
        import openai
        
        # 設置模擬超時錯誤
        model.client.chat.completions.create = AsyncMock(
            side_effect=openai.APITimeoutError("Request timed out")
        )
        
        with pytest.raises(ModelError) as exc_info:
            await model.generate("Test prompt")
        
        assert "Request timed out" in str(exc_info.value) 