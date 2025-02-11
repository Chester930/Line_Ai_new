import pytest
from unittest.mock import patch, Mock
from src.shared.ai.models.gemini import GeminiModel
from src.shared.ai.base import ModelType

@pytest.fixture
def mock_genai():
    """模擬 Google AI"""
    with patch('src.shared.ai.models.gemini.genai') as mock:
        mock.GenerativeModel.return_value = Mock()
        yield mock

@pytest.fixture
def gemini_model(mock_genai):
    """創建 Gemini 模型實例"""
    return GeminiModel()

@pytest.mark.asyncio
async def test_text_generation(gemini_model, mock_genai):
    """測試文本生成"""
    mock_response = Mock()
    mock_response.text = "測試響應"
    mock_response.dict.return_value = {"response": "data"}
    
    mock_model = mock_genai.GenerativeModel.return_value
    mock_model.generate_content_async.return_value = mock_response
    
    response = await gemini_model.generate("測試提示")
    
    assert response.text == "測試響應"
    assert response.model == ModelType.GEMINI
    assert response.raw_response == {"response": "data"}

@pytest.mark.asyncio
async def test_image_analysis(gemini_model, mock_genai):
    """測試圖片分析"""
    mock_response = Mock()
    mock_response.text = "圖片描述"
    mock_response.dict.return_value = {"response": "data"}
    
    mock_model = Mock()
    mock_model.generate_content_async.return_value = mock_response
    mock_genai.GenerativeModel.return_value = mock_model
    
    response = await gemini_model.analyze_image(b"image_data")
    
    assert response.text == "圖片描述"
    assert response.model == ModelType.GEMINI

@pytest.mark.asyncio
async def test_error_handling(gemini_model, mock_genai):
    """測試錯誤處理"""
    mock_model = mock_genai.GenerativeModel.return_value
    mock_model.generate_content_async.side_effect = Exception("API 錯誤")
    
    response = await gemini_model.generate("測試提示")
    
    assert response.error == "API 錯誤"
    assert response.text == "" 