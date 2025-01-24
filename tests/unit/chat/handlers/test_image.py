import pytest
from unittest.mock import patch, Mock
from src.shared.chat.handlers.image import ImageMessageHandler
from src.shared.chat.session import Message
from src.shared.ai.base import AIResponse, ModelType

@pytest.fixture
def image_handler():
    return ImageMessageHandler()

@pytest.fixture
def image_message():
    return Message(
        content="",
        role="user",
        type="image",
        media_url="http://example.com/test.jpg"
    )

@pytest.mark.asyncio
async def test_image_validation(image_handler, image_message):
    """測試圖片驗證"""
    assert await image_handler.validate(image_message)
    
    # 測試無 URL
    no_url = Message(content="", role="user", type="image")
    assert not await image_handler.validate(no_url)
    
    # 測試錯誤類型
    wrong_type = Message(content="", role="user", type="text")
    assert not await image_handler.validate(wrong_type)

@pytest.mark.asyncio
async def test_image_processing(image_handler, image_message):
    """測試圖片處理"""
    mock_response = AIResponse(
        text="image description",
        model=ModelType.GEMINI,
        tokens=5
    )
    
    with patch('aiohttp.ClientSession') as mock_session, \
         patch('src.shared.ai.factory.AIModelFactory.create') as mock_create:
        # 模擬圖片下載
        mock_get = Mock()
        mock_get.status = 200
        mock_get.read = Mock(return_value=b"image_data")
        mock_session.return_value.__aenter__.return_value.get.return_value.__aenter__.return_value = mock_get
        
        # 模擬 AI 模型
        mock_model = Mock()
        mock_model.analyze_image.return_value = mock_response
        mock_create.return_value = mock_model
        
        result = await image_handler.handle(image_message)
        
        assert result["success"]
        assert result["response"] == "image description"
        assert result["model"] == "gemini"
        assert result["tokens"] == 5 