import pytest
from unittest.mock import Mock, patch
from plugins.image_analyzer import ImageAnalyzerPlugin
from src.shared.plugins.base import PluginConfig

class TestImageAnalyzerPlugin:
    def setup_method(self):
        self.config = PluginConfig(
            name="image_analyzer",
            version="1.0",
            settings={
                "api_key": "test_key",
                "model": "test-model"
            }
        )
        self.plugin = ImageAnalyzerPlugin(self.config)
    
    @pytest.mark.asyncio
    async def test_initialize(self):
        assert await self.plugin.initialize()
        assert self.plugin.api_key == "test_key"
        assert self.plugin.model == "test-model"
    
    @pytest.mark.asyncio
    @patch('aiohttp.ClientSession.post')
    async def test_analyze_image(self, mock_post):
        # 設置模擬回應
        mock_response = Mock()
        mock_response.json.return_value = {
            "candidates": [{
                "content": {
                    "parts": [{"text": "A beautiful landscape"}]
                }
            }]
        }
        mock_post.return_value.__aenter__.return_value = mock_response
        
        # 執行分析
        result = await self.plugin.execute({
            "image": "base64_encoded_image_data",
            "prompt": "Describe this image"
        })
        
        # 驗證結果
        assert result["success"]
        assert "description" in result
        assert result["description"] == "A beautiful landscape"
    
    @pytest.mark.asyncio
    async def test_missing_image(self):
        result = await self.plugin.execute({})
        assert not result["success"]
        assert "error" in result 