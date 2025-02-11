import pytest
from unittest.mock import AsyncMock, patch
from src.shared.ai.base import BaseAIModel
from src.shared.ai.models.gemini import GeminiModel
from src.shared.ai.factory import AIModelFactory
from src.shared.config.base import ConfigManager

class TestAIModels:
    @pytest.fixture
    def config(self):
        """配置測試夾具"""
        config = ConfigManager()
        config.set("GOOGLE_API_KEY", "test_api_key")
        return config
        
    @pytest.fixture
    def gemini_model(self, config):
        """Gemini 模型測試夾具"""
        return GeminiModel(config)
        
    @pytest.mark.asyncio
    async def test_text_generation(self, gemini_model):
        """測試文本生成"""
        with patch('google.generativeai.GenerativeModel.generate_content', new_callable=AsyncMock) as mock_generate:
            mock_generate.return_value.text = "Generated response"
            
            response = await gemini_model.generate_text(
                prompt="Hello, AI!",
                max_tokens=100
            )
            
            assert response == "Generated response"
            mock_generate.assert_called_once()
            
    @pytest.mark.asyncio
    async def test_image_analysis(self, gemini_model):
        """測試圖片分析"""
        with patch('google.generativeai.GenerativeModel.generate_content', new_callable=AsyncMock) as mock_generate:
            mock_generate.return_value.text = "Image analysis result"
            
            response = await gemini_model.analyze_image(
                image_url="https://example.com/image.jpg",
                prompt="Describe this image"
            )
            
            assert response == "Image analysis result"
            mock_generate.assert_called_once()
            
    @pytest.mark.asyncio
    async def test_error_handling(self, gemini_model):
        """測試錯誤處理"""
        with patch('google.generativeai.GenerativeModel.generate_content', new_callable=AsyncMock) as mock_generate:
            mock_generate.side_effect = Exception("API Error")
            
            with pytest.raises(Exception) as exc_info:
                await gemini_model.generate_text("Should fail")
                
            assert "API Error" in str(exc_info.value)
            
    def test_model_factory(self, config):
        """測試模型工廠"""
        # 註冊模型
        @AIModelFactory.register("test_model")
        class TestModel(BaseAIModel):
            async def generate_text(self, prompt: str, **kwargs):
                return "Test response"
                
        # 創建模型實例
        model = AIModelFactory.create("test_model", config)
        assert isinstance(model, TestModel)
        
    @pytest.mark.asyncio
    async def test_context_management(self, gemini_model):
        """測試上下文管理"""
        with patch('google.generativeai.GenerativeModel.generate_content', new_callable=AsyncMock) as mock_generate:
            mock_generate.return_value.text = "Response with context"
            
            # 設置上下文
            gemini_model.set_context([
                {"role": "user", "content": "Previous message"},
                {"role": "assistant", "content": "Previous response"}
            ])
            
            response = await gemini_model.generate_text("Next message")
            assert response == "Response with context"
            
            # 驗證上下文被正確使用
            call_args = mock_generate.call_args[0]
            assert len(call_args[0]) > 1  # 應該包含上下文消息
            
    @pytest.mark.asyncio
    async def test_streaming_response(self, gemini_model):
        """測試流式響應"""
        async def mock_stream():
            yield "Part 1"
            yield "Part 2"
            yield "Part 3"
            
        with patch('google.generativeai.GenerativeModel.generate_content', new_callable=AsyncMock) as mock_generate:
            mock_generate.return_value.text_stream = mock_stream
            
            responses = []
            async for chunk in gemini_model.generate_stream("Stream test"):
                responses.append(chunk)
                
            assert len(responses) == 3
            assert responses == ["Part 1", "Part 2", "Part 3"] 