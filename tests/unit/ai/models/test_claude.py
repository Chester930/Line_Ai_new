import pytest
from unittest.mock import Mock, patch, AsyncMock
from src.shared.ai.models.claude import ClaudeModel, ClaudeConfig
from src.shared.ai.base import ModelResponse, Message
from src.shared.exceptions import ModelError

class TestClaudeModel:
    @pytest.fixture
    def config(self):
        return ClaudeConfig(
            name="claude",
            api_key="test_key",
            model_name="claude-3-opus-20240229",
            max_tokens=1000,
            temperature=0.7,
            request_timeout=30
        )
    
    @pytest.fixture
    async def model(self, config):
        with patch('anthropic.AsyncAnthropic') as mock_anthropic:
            model = ClaudeModel(config)
            yield model
            # 清理資源
            await model.client.close()
    
    @pytest.mark.asyncio
    async def test_initialize(self, model):
        """測試模型初始化"""
        assert model.name == "claude"
        assert model.config.api_key == "test_key"
        assert model.config.model_name == "claude-3-opus-20240229"
    
    @pytest.mark.asyncio
    async def test_generate_success(self, model):
        """測試成功生成回應"""
        # 設置模擬回應
        mock_response = Mock()
        mock_response.content = [Mock(text="Test response")]
        mock_response.usage = Mock(
            input_tokens=10,
            output_tokens=20
        )
        mock_response.stop_reason = "stop"
        mock_response.stop_sequence = None
        
        # 設置模擬客戶端
        model.client.messages.create = AsyncMock(
            return_value=mock_response
        )
        
        # 執行生成
        result = await model.generate("Test prompt")
        
        # 驗證結果
        assert isinstance(result, ModelResponse)
        assert result.text == "Test response"
        assert result.usage["total_tokens"] == 30
        assert result.model_info["model"] == "claude-3-opus-20240229"
        assert result.model_info["stop_reason"] == "stop"
    
    @pytest.mark.asyncio
    async def test_generate_with_context(self, model):
        """測試帶上下文生成"""
        # 設置模擬回應
        mock_response = Mock()
        mock_response.content = [Mock(text="Test response")]
        mock_response.usage = Mock(
            input_tokens=15,
            output_tokens=25
        )
        mock_response.stop_reason = "stop"
        
        # 設置模擬客戶端
        model.client.messages.create = AsyncMock(
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
        create_args = model.client.messages.create.call_args[1]
        assert "messages" in create_args
        assert len(create_args["messages"]) == 3
    
    @pytest.mark.asyncio
    async def test_generate_stream(self, model):
        """測試流式生成"""
        # 設置模擬流式回應
        mock_chunks = [
            Mock(delta=Mock(text="Hello")),
            Mock(delta=Mock(text=" world")),
            Mock(delta=Mock(text="!"))
        ]
        
        # 設置模擬客戶端
        model.client.messages.create = AsyncMock(return_value=mock_chunks)
        
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
        # 設置模擬回應
        mock_response = Mock(count=5)
        model.client.count_tokens = AsyncMock(return_value=mock_response)
        
        count = await model.count_tokens("Hello, world!")
        assert count == 5
    
    @pytest.mark.asyncio
    async def test_error_handling(self, model):
        """測試錯誤處理"""
        # 設置模擬錯誤
        model.client.messages.create = AsyncMock(
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
        mock_response.content = [Mock(text="Test")]
        model.client.messages.create = AsyncMock(
            return_value=mock_response
        )
        
        is_valid = await model.validate()
        assert is_valid is True
        
        # 測試驗證失敗
        model.client.messages.create = AsyncMock(
            side_effect=Exception("Test error")
        )
        is_valid = await model.validate()
        assert is_valid is False
    
    @pytest.mark.asyncio
    async def test_system_prompt(self, model):
        """測試系統提示詞"""
        # 設置模擬回應
        mock_response = Mock()
        mock_response.content = [Mock(text="Test response")]
        mock_response.usage = Mock(
            input_tokens=10,
            output_tokens=20
        )
        
        # 設置模擬客戶端
        model.client.messages.create = AsyncMock(
            return_value=mock_response
        )
        
        # 執行生成
        await model.generate("Test prompt")
        
        # 驗證系統提示詞
        create_args = model.client.messages.create.call_args[1]
        assert "system" in create_args
        assert create_args["system"] == "You are Claude, a helpful AI assistant." 