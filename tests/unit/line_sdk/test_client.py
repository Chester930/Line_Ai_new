import pytest
from unittest.mock import Mock, patch, AsyncMock
from linebot.v3.messaging import MessagingApi
from linebot.v3.webhook import WebhookParser
from src.shared.line_sdk.client import LineClient, line_client

class MockSettings:
    def __init__(self):
        self.line_channel_secret = "test_secret"
        self.line_channel_access_token = "test_token"

@pytest.fixture(autouse=True)
def mock_config():
    """模擬配置"""
    mock_settings = MockSettings()
    with patch('src.shared.line_sdk.client.config') as mock:
        mock.settings = mock_settings
        yield mock

def test_line_client_singleton():
    """測試 LINE 客戶端單例模式"""
    client1 = LineClient()
    client2 = LineClient()
    assert client1 is client2

def test_line_client_initialization():
    """測試 LINE 客戶端初始化"""
    client = LineClient()
    client.initialized = False
    client.__init__()
    assert isinstance(client.messaging_api, MessagingApi)
    assert isinstance(client.parser, WebhookParser)

@pytest.mark.asyncio
async def test_send_message():
    """測試發送消息"""
    user_id = "test_user"
    message = "test_message"
    mock_api = AsyncMock()
    with patch.object(line_client, 'messaging_api', mock_api):
        await line_client.send_message(user_id, message)
        mock_api.push_message.assert_called_once_with(user_id, message)

@pytest.mark.asyncio
async def test_reply_message():
    """測試回覆消息"""
    reply_token = "test_token"
    message = "test_message"
    
    mock_api = AsyncMock()
    with patch.object(line_client, 'messaging_api', mock_api):
        await line_client.reply_message(reply_token, message)
        mock_api.reply_message.assert_called_once_with(reply_token, message)

def test_verify_webhook():
    """測試 webhook 驗證"""
    body = b"test_body"
    signature = "valid_signature"
    with patch.object(line_client.parser.signature_validator, 'validate', return_value=True):
        assert line_client.verify_webhook(body, signature) is True

def test_parse_webhook_body():
    """測試解析 webhook 請求體"""
    body = b"test_body"
    mock_events = [Mock(), Mock()]
    
    with patch.object(line_client.parser, 'parse', return_value=mock_events):
        events = line_client.parse_webhook_body(body)
        assert events == mock_events