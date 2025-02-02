import pytest
from unittest.mock import Mock, patch, AsyncMock, create_autospec, MagicMock
from src.shared.ai.models.gemini import GeminiModel, GeminiConfig
from src.shared.ai.base import ModelResponse, Message
from src.shared.exceptions import ModelError

@pytest.fixture
def config():
    return GeminiConfig(
        api_key="test_key",
        name="gemini",
        model_name="gemini-pro",
        temperature=0.7,
        max_tokens=1000
    )

@pytest.fixture
async def model(config):
    with patch('google.generativeai.GenerativeModel') as mock_genai:
        model = GeminiModel(config)
        model.client = AsyncMock()
        yield model

@pytest.mark.asyncio
class TestGeminiModel:
    async def test_initialization_error(self, config):
        """測試初始化錯誤處理"""
        with patch('google.generativeai.GenerativeModel', side_effect=Exception("Init error")):
            with pytest.raises(ModelError) as exc_info:
                GeminiModel(config)
            assert "Initialization failed" in str(exc_info.value)

    async def test_generate_with_context(self, model):
        """測試帶上下文生成"""
        mock_response = AsyncMock()
        mock_response.text = "Test response"
        mock_response.prompt_token_count = 10
        mock_response.candidates = [AsyncMock(token_count=20)]
        model.client.generate_content = AsyncMock(return_value=mock_response)

        context = [
            {"role": "user", "content": "Previous message"},
            {"role": "assistant", "content": "Previous response"}
        ]
        response = await model.generate("Test prompt", context=context)
        
        assert response.text == "Test response"
        assert response.usage["total_tokens"] == 30

    @pytest.mark.asyncio
    async def test_initialize(self, model):
        """測試初始化"""
        assert model.name == "gemini"
        assert model.config.api_key == "test_key"
        assert model.config.model_name == "gemini-pro"
    
    @pytest.mark.asyncio
    async def test_generate_success(self, model):
        """測試成功生成回應"""
        # 設置模擬回應
        mock_response = Mock()
        mock_response.text = "Test response"
        mock_response.prompt_token_count = 10
        mock_response.candidates = [Mock(token_count=20)]
        
        model.client.generate_content = AsyncMock(return_value=mock_response)
        
        result = await model.generate("Test prompt")
        
        assert isinstance(result, ModelResponse)
        assert result.text == "Test response"
        assert result.usage["total_tokens"] == 30
        assert result.model_info["model"] == "gemini-pro"
    
    @pytest.mark.asyncio
    async def test_generate_stream(self, model):
        """測試流式生成"""
        # 設置模擬流式回應
        mock_chunks = [
            Mock(text="Hello"),
            Mock(text=" world"),
            Mock(text="!")
        ]
        
        # 修改異步迭代器的模擬方式
        async def mock_stream(self, *args, **kwargs):  # 添加 self 參數
            for chunk in mock_chunks:
                yield chunk
        
        # 創建一個異步 mock 對象
        mock_response = AsyncMock()
        mock_response.__aiter__ = mock_stream
        mock_response.__call__ = AsyncMock(return_value=mock_response)  # 添加這行
        
        model.client.generate_content = AsyncMock(return_value=mock_response)
        
        messages = [
            Message(
                id=1,
                user_id="test",
                content="Hi",
                role="user",
                type="text"
            )
        ]
        
        # 收集生成的文本
        chunks = []
        async for chunk in model.generate_stream(messages):
            chunks.append(chunk)
        
        # 驗證結果
        assert len(chunks) == 3
        assert "".join(chunks) == "Hello world!"
        
        # 驗證調用參數
        model.client.generate_content.assert_called_once()
        call_args = model.client.generate_content.call_args
        assert call_args[1]["stream"] is True
        assert len(call_args[0][0]) == 1  # 检查消息列表长度
        assert call_args[0][0][0]["role"] == "user"
        assert call_args[0][0][0]["parts"] == ["Hi"]  # 直接检查内容
    
    @pytest.mark.asyncio
    async def test_analyze_image(self, model, tmp_path):
        """測試圖片分析"""
        # 創建測試圖片
        image_path = tmp_path / "test.jpg"
        image_path.write_bytes(b"test image content")
        
        with open(image_path, "rb") as f:
            image_bytes = f.read()
        
        response = await model.analyze_image(
            image_bytes,
            prompt="描述這張圖片"
        )
        
        assert response is not None
        assert isinstance(response.text, str)
        assert response.model == model.config.model_name
    
    @pytest.mark.asyncio
    async def test_error_handling(self, model):
        """測試錯誤處理"""
        model.client.generate_content = AsyncMock(
            side_effect=Exception("Test error")
        )
        
        with pytest.raises(ModelError) as exc_info:
            await model.generate("Test prompt")
        
        assert "Generation failed: Test error" in str(exc_info.value)
    
    @pytest.mark.asyncio
    async def test_validate(self, model):
        """測試模型驗證"""
        # 設置模擬成功回應
        mock_response = Mock()
        mock_response.text = "Test response"
        mock_response.prompt_token_count = 10
        mock_response.candidates = [Mock(token_count=20)]
        
        model.client.generate_content = AsyncMock(return_value=mock_response)
        
        is_valid = await model.validate()
        assert is_valid is True
        
        # 測試驗證失敗
        model.client.generate_content = AsyncMock(
            side_effect=Exception("Test error")
        )
        is_valid = await model.validate()
        assert is_valid is False
    
    @pytest.mark.asyncio
    async def test_validate_response(self, model):
        """測試響應驗證"""
        valid_response = {"text": "Valid response"}
        assert await model.validate_response(valid_response) is True
        
        invalid_response = {}
        assert await model.validate_response(invalid_response) is False

    @pytest.mark.asyncio
    async def test_stream_error_handling(self, model):
        """測試流式生成錯誤處理"""
        model.client.generate_content = AsyncMock(
            side_effect=Exception("Stream error")
        )
        
        messages = [
            Message(
                id=1,
                user_id="test",
                content="Hi",
                role="user",
                type="text"
            )
        ]
        
        with pytest.raises(ModelError) as exc_info:
            async for _ in model.generate_stream(messages):
                pass
        
        assert "Stream generation failed" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_image_analysis_error(self, model):
        """測試圖片分析錯誤處理"""
        model.client.generate_content = AsyncMock(
            side_effect=Exception("Image analysis error")
        )
        
        response = await model.analyze_image(
            b"invalid image",
            prompt="描述圖片"
        )
        
        assert "很抱歉，處理過程中發生錯誤" in response.text
        assert response.tokens == 0

    @pytest.mark.asyncio
    async def test_count_tokens_error(self, model):
        """測試計算 tokens 錯誤處理"""
        model.client.count_tokens = Mock(side_effect=Exception("Token count error"))
        
        with pytest.raises(Exception) as exc_info:
            await model.count_tokens("Test text")
        assert "Token count error" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_handle_error(self, model):
        """測試統一錯誤處理"""
        error = Exception("Test error")
        response = await model.handle_error(error)
        
        assert isinstance(response.text, str)
        assert "很抱歉" in response.text
        assert response.model == model.config.model_name
        assert response.tokens == 0
        assert "error" in response.raw_response 

    @pytest.mark.asyncio
    async def test_format_messages(self, model):
        """測試消息格式化"""
        messages = [
            Message(
                id=1,
                role="user",
                content="Hello",
                user_id="test",
                type="text"
            ),
            Message(
                id=2,
                role="assistant",
                content="Hi",
                user_id="test",
                type="text"
            )
        ]
        
        formatted = model._format_messages(messages)
        assert len(formatted) == 2
        assert formatted[0]["role"] == "user"
        assert formatted[0]["parts"] == ["Hello"]
        assert formatted[1]["role"] == "assistant"
        assert formatted[1]["parts"] == ["Hi"]

    @pytest.mark.asyncio
    async def test_build_prompt(self, model):
        """測試提示詞構建"""
        messages = [
            {"role": "user", "content": "Hello"},
            {"role": "assistant", "content": "Hi"},
            {"role": "user", "content": "How are you?"}
        ]
        
        prompt = model._build_prompt(messages)
        expected = "User: Hello\nAssistant: Hi\nUser: How are you?\nAssistant: "
        assert prompt == expected

    @pytest.mark.asyncio
    async def test_generate_response(self, model):
        """測試生成回應"""
        # 創建一個完整的 mock 響應類
        class MockResponse:
            def __init__(self, text):
                self._text = text
                self._content = text
                self._parts = [{"text": text}]
                
            @property
            def text(self):
                return self._text
                
            @property
            def content(self):
                return self._content
                
            @property
            def parts(self):
                return self._parts
                
            def dict(self):
                return {
                    "text": self._text,
                    "content": self._content,
                    "parts": self._parts
                }
                
            def __getattr__(self, name):
                # 處理未知屬性
                if name in self.__dict__:
                    return self.__dict__[name]
                return None
        
        # 創建 mock 響應
        mock_response = MockResponse("I'm fine, thank you!")
        model.client.generate_content = AsyncMock(return_value=mock_response)
        
        # 測試正常響應
        messages = [Message(
            id=1,
            role="user",
            content="How are you?",
            user_id="test",
            type="text"
        )]
        response = await model.generate_response(messages)
        assert response == "I'm fine, thank you!"
        
        # 測試錯誤處理
        model.client.generate_content = AsyncMock(side_effect=Exception("Error"))
        response = await model.generate_response(messages)
        assert "錯誤" in response
        
        # 測試空響應處理
        empty_response = MockResponse("")
        model.client.generate_content = AsyncMock(return_value=empty_response)
        response = await model.generate_response(messages)
        assert response == ""

    @pytest.mark.asyncio
    async def test_generate_response_edge_cases(self, model):
        """測試生成回應的邊界情況"""
        # 測試不同的響應格式
        responses = [
            # 只有 text
            AsyncMock(text="Response 1"),
            # 只有 content
            AsyncMock(content="Response 2"),
            # 有字典方法
            AsyncMock(dict=lambda: {"text": "Response 3"}),
            # 空響應
            AsyncMock(text="", content="")
        ]
        
        for i, mock_response in enumerate(responses):
            model.client.generate_content = AsyncMock(return_value=mock_response)
            response = await model.generate_response([{"role": "user", "content": "test"}])
            assert response and isinstance(response, str), f"Case {i} failed"

def test_config_defaults():
    """測試配置默認值"""
    config = GeminiConfig(api_key="test_key")
    assert config.name == "gemini"
    assert config.model_name == "gemini-pro"
    assert config.max_tokens == 1000
    assert config.temperature == 0.7
    assert config.top_p == 0.95
    assert config.top_k == 40

def test_config_validation_ranges():
    """測試配置值範圍驗證"""
    # 測試溫度範圍
    with pytest.raises(ValueError):
        GeminiConfig(api_key="test_key", temperature=-0.1)
    with pytest.raises(ValueError):
        GeminiConfig(api_key="test_key", temperature=1.1)
        
    # 測試 top_p 範圍
    with pytest.raises(ValueError):
        GeminiConfig(api_key="test_key", top_p=-0.1)
    with pytest.raises(ValueError):
        GeminiConfig(api_key="test_key", top_p=1.1)
        
    # 測試 max_tokens 範圍
    with pytest.raises(ValueError):
        GeminiConfig(api_key="test_key", max_tokens=0) 