import pytest
from unittest.mock import Mock, patch, AsyncMock
from linebot.v3.messaging import MessagingApi
from linebot.v3.webhook import WebhookParser
from src.shared.line_sdk.client import LineClient

@pytest.fixture(autouse=True)
def mock_settings():
    """模擬配置"""
    with patch('src.shared.config.config.settings') as mock:
        mock.LINE_CHANNEL_SECRET = "test_secret"
        mock.LINE_CHANNEL_ACCESS_TOKEN = "test_token"
        yield mock

@pytest.fixture
def line_client():
    """創建 LINE 客戶端實例"""
    return LineClient()

def test_line_client_singleton():
    """測試 LINE 客戶端單例模式"""
    client1 = LineClient()
    client2 = LineClient()
    assert client1 is client2

def test_line_client_initialization():
    """測試 LINE 客戶端初始化"""
    client = LineClient()
    assert client.messaging_api is not None
    assert client.parser is not None

@pytest.mark.asyncio
async def test_reply_message(line_client):
    """測試回覆消息"""
    with patch.object(line_client.messaging_api, 'reply_message', AsyncMock()) as mock_reply:
        reply_token = "test_reply_token"
        message = "Hello, World!"
        await line_client.reply_message(reply_token, message)
        mock_reply.assert_awaited_once()

@pytest.mark.asyncio
async def test_send_message(line_client):
    """測試發送消息"""
    with patch.object(line_client.messaging_api, 'push_message', AsyncMock()) as mock_send:
        user_id = "test_user_id"
        message = "Hello, User!"
        await line_client.send_message(user_id, message)
        mock_send.assert_awaited_once()

@pytest.mark.asyncio
async def test_get_profile(line_client):
    """測試獲取用戶資料"""
    mock_profile = Mock()
    mock_profile.display_name = "Test User"
    mock_profile.user_id = "test_user_id"
    mock_profile.picture_url = "http://example.com/picture.jpg"
    mock_profile.status_message = "Test Status"
    
    with patch.object(line_client.messaging_api, 'get_profile', AsyncMock(return_value=mock_profile)) as mock_get:
        user_id = "test_user_id"
        profile = await line_client.get_profile(user_id)
        mock_get.assert_awaited_once_with(user_id)
        assert isinstance(profile, dict)
        assert profile["user_id"] == "test_user_id"
        assert profile["display_name"] == "Test User"

def test_verify_webhook(line_client):
    """測試驗證 webhook 簽名"""
    with patch.object(line_client.parser.signature_validator, 'validate', return_value=True):
        body = b"test_body"
        signature = "test_signature"
        result = line_client.verify_webhook(body, signature)
        assert result is True

def test_verify_webhook_failure(line_client):
    """測試驗證 webhook 簽名失敗"""
    with patch.object(line_client.parser.signature_validator, 'validate', side_effect=Exception("驗證失敗")):
        body = b"test_body"
        signature = "test_signature"
        result = line_client.verify_webhook(body, signature)
        assert result is False

def test_parse_webhook_body(line_client):
    """測試解析 webhook 請求體"""
    expected_result = {"type": "message"}
    with patch.object(line_client.parser, 'parse', return_value=expected_result):
        body = b"test_body"
        result = line_client.parse_webhook_body(body)
        assert result == expected_result

@pytest.mark.asyncio
async def test_line_client():
    """測試 LINE 客戶端"""
    client = LineClient(channel_access_token="test_token")
    assert client.channel_access_token == "test_token"