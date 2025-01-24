import pytest
from unittest.mock import Mock, patch
from src.line.client import LineBotClient
from src.line.handler import LineBotHandler
from linebot.models import MessageEvent, TextMessage, TextSendMessage

@pytest.fixture
def line_client():
    """LINE Bot 客戶端"""
    return LineBotClient()

@pytest.fixture
def line_handler():
    """LINE Bot 處理器"""
    return LineBotHandler()

@pytest.mark.asyncio
async def test_send_text_message(line_client):
    """測試發送文字消息"""
    with patch.object(line_client.client, 'push_message') as mock_push:
        # 發送消息
        success = await line_client.send_text(
            "test_user",
            "Hello, World!"
        )
        
        # 驗證
        assert success
        mock_push.assert_called_once()
        args = mock_push.call_args[0]
        assert args[0] == "test_user"
        assert isinstance(args[1], TextSendMessage)
        assert args[1].text == "Hello, World!"

@pytest.mark.asyncio
async def test_get_profile(line_client):
    """測試獲取用戶資料"""
    with patch.object(line_client.client, 'get_profile') as mock_get:
        # 模擬用戶資料
        mock_profile = Mock(
            user_id="test_user",
            display_name="Test User",
            picture_url="http://example.com/pic.jpg",
            status_message="Hello!"
        )
        mock_get.return_value = mock_profile
        
        # 獲取資料
        profile = await line_client.get_profile("test_user")
        
        # 驗證
        assert profile is not None
        assert profile["user_id"] == "test_user"
        assert profile["display_name"] == "Test User"

@pytest.mark.asyncio
async def test_webhook_handling(line_handler):
    """測試 webhook 處理"""
    # 模擬請求
    mock_request = Mock()
    mock_body = '{"events": []}'
    mock_signature = "test_signature"
    
    with patch.object(line_handler.handler, 'handle') as mock_handle:
        # 處理請求
        success = await line_handler.handle_request(
            mock_request,
            mock_body,
            mock_signature
        )
        
        # 驗證
        assert success
        mock_handle.assert_called_once_with(mock_body, mock_signature)

def test_message_event_handling(line_handler):
    """測試消息事件處理"""
    # 模擬文字消息事件
    mock_event = Mock(spec=MessageEvent)
    mock_event.message = Mock(spec=TextMessage)
    mock_event.message.text = "Hello"
    mock_event.source.user_id = "test_user"
    
    # 處理事件
    response = line_handler.handler._handlers[MessageEvent](mock_event)
    
    # 驗證
    assert isinstance(response, TextSendMessage)
    assert response.text == "Hello" 