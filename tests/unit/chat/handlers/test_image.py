import pytest
from unittest.mock import patch, AsyncMock
from aioresponses import aioresponses
from src.shared.chat.handlers.image import ImageMessageHandler
from src.shared.chat.session import Message
from src.shared.ai.base import AIResponse, ModelType
import aiohttp

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

@pytest.fixture
def mock_aioresponse():
    with aioresponses() as m:
        yield m

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
async def test_image_processing(image_handler, image_message, mock_aioresponse):
    """測試圖片處理"""
    mock_response = AIResponse(
        content="image description",
        model=ModelType.GEMINI,
        tokens=5
    )
    
    # 模擬 HTTP 響應
    mock_aioresponse.get(
        image_message.media_url,
        status=200,
        body=b"image_data"
    )
    
    with patch('src.shared.ai.factory.AIModelFactory.create') as mock_create:
        mock_model = AsyncMock()
        mock_model.analyze_image = AsyncMock(return_value=mock_response)
        mock_create.return_value = mock_model
        
        result = await image_handler.handle(image_message)
        assert result["success"]
        assert result["response"] == "image description"
        assert result["model"] == "gemini"
        assert result["tokens"] == 5

@pytest.mark.asyncio
async def test_image_download(image_handler, image_message, mock_aioresponse):
    """測試圖片下載"""
    mock_content = b"fake_image_data"
    
    # 模擬 HTTP 響應
    mock_aioresponse.get(
        image_message.media_url,
        status=200,
        body=mock_content
    )
    
    processed = await image_handler.preprocess(image_message)
    assert processed.content == mock_content

@pytest.mark.asyncio
async def test_image_download_error(image_handler, image_message, mock_aioresponse):
    """測試圖片下載錯誤"""
    # 模擬 HTTP 錯誤
    mock_aioresponse.get(
        image_message.media_url,
        status=404
    )
    
    with pytest.raises(ValueError, match="下載圖片失敗: HTTP 404"):
        await image_handler.preprocess(image_message)

@pytest.mark.asyncio
async def test_image_download_network_error(image_handler, image_message):
    """測試圖片下載網絡錯誤"""
    with patch('aiohttp.ClientSession') as mock_session:
        mock_session.return_value = AsyncMock(
            __aenter__=AsyncMock(side_effect=aiohttp.ClientError("Network error"))
        )
        
        with pytest.raises(Exception) as exc_info:
            await image_handler.preprocess(image_message)
        assert "Network error" in str(exc_info.value)

@pytest.mark.asyncio
async def test_image_processing_error(image_handler, image_message, mock_aioresponse):
    """測試圖片處理錯誤"""
    # 模擬成功下載圖片
    mock_aioresponse.get(
        image_message.media_url,
        status=200,
        body=b"image_data"
    )
    
    with patch('src.shared.ai.factory.AIModelFactory.create') as mock_create:
        mock_model = AsyncMock()
        mock_model.analyze_image = AsyncMock(side_effect=Exception("AI processing error"))
        mock_create.return_value = mock_model
        
        result = await image_handler.handle(image_message)
        assert not result["success"]
        assert "AI processing error" in result["error"]
        assert result["response"] is None 