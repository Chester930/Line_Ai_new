import pytest
from unittest.mock import Mock, patch, AsyncMock
from fastapi import Request
from linebot.v3.webhook import WebhookHandler
from linebot.v3.messaging.models import TextMessage
from linebot.models import TextSendMessage
from linebot.v3.webhooks import MessageEvent
from src.line.handler import LineBotHandler
from src.shared.config.config import settings
from src.shared.events.types import MessageEvent as AppMessageEvent
from linebot.v3.webhook import WebhookParser
from src.shared.line_sdk.webhook import WebhookParser
from src.shared.exceptions import ValidationError

@pytest.fixture
def webhook_handler():
    """創建 LINE Bot 處理器實例"""
    return LineBotHandler()

@pytest.fixture
def webhook_parser():
    """創建 Webhook 解析器實例"""
    with patch('src.shared.config.config.settings') as mock_settings:
        mock_settings.LINE_CHANNEL_SECRET = "test_secret"
        parser = WebhookParser(channel_secret="test_secret")
        return parser

def test_handler_initialization(webhook_handler):
    """測試處理器初始化"""
    assert webhook_handler.handler is not None
    assert isinstance(webhook_handler.handler, WebhookHandler)

@pytest.mark.asyncio
async def test_handle_text_message(webhook_handler):
    """測試處理文字消息"""
    # 創建測試數據
    mock_event = Mock(spec=MessageEvent)
    mock_event.message = Mock(spec=TextMessage)
    mock_event.message.text = "Hello, World!"
    mock_event.message.id = "test_message_id"
    mock_event.source = Mock()
    mock_event.source.user_id = "test_user_id"
    
    # 模擬事件發布器
    with patch('src.line.handler.event_publisher') as mock_publisher:
        mock_publisher.publish = AsyncMock()
        
        # 直接調用處理函數
        result = await webhook_handler.handle_message(mock_event)
        
        # 驗證結果
        assert isinstance(result, TextSendMessage)
        assert result.text == "Hello, World!"
        
        # 驗證事件發布
        mock_publisher.publish.assert_awaited_once()
        actual_event = mock_publisher.publish.call_args[0][0]
        assert actual_event.data['message_id'] == "test_message_id"
        assert actual_event.data['user_id'] == "test_user_id"
        assert actual_event.data['content'] == "Hello, World!"

@pytest.mark.asyncio
async def test_handle_request(webhook_handler):
    """測試處理 webhook 請求"""
    # 創建模擬請求
    mock_request = Mock()
    body = "test_body"
    signature = "test_signature"
    
    # 模擬 handler.handle
    with patch.object(webhook_handler.handler, 'handle', AsyncMock()) as mock_handle:
        # 測試成功情況
        result = await webhook_handler.handle_request(mock_request, body, signature)
        assert result is True
        mock_handle.assert_awaited_once_with(body, signature)

@pytest.mark.asyncio
async def test_handle_request_error(webhook_handler):
    """測試處理 webhook 請求錯誤"""
    mock_request = Mock()
    body = "test_body"
    signature = "test_signature"
    
    with patch.object(webhook_handler.handler, 'handle', AsyncMock(side_effect=Exception("Test error"))):
        result = await webhook_handler.handle_request(mock_request, body, signature)
        assert result is False

def test_webhook_parser_initialization(webhook_parser):
    """測試 Webhook 解析器初始化"""
    assert webhook_parser.line_parser is not None
    assert webhook_parser.signature_validator is not None

@pytest.mark.asyncio
async def test_parse_webhook_events(webhook_parser):
    """測試解析 webhook 事件"""
    mock_events = [
        {
            "type": "message",
            "message": {"type": "text", "text": "Hello"},
            "source": {"type": "user", "userId": "test_user"}
        }
    ]
    
    with patch.object(webhook_parser.line_parser, 'parse', return_value=mock_events):
        events = webhook_parser.parse(b"test_body")
        assert len(events) == 1
        assert events[0]["type"] == "message"
        assert events[0]["message"]["text"] == "Hello"

def test_verify_webhook_signature(webhook_parser):
    """測試驗證 webhook 簽名"""
    with patch.object(webhook_parser.signature_validator, 'validate', return_value=True):
        result = webhook_parser.verify_signature(b"test_body", "test_signature")
        assert result is True

def test_verify_webhook_signature_failure(webhook_parser):
    """測試驗證 webhook 簽名失敗"""
    with patch.object(webhook_parser.signature_validator, 'validate', side_effect=Exception("Invalid signature")):
        result = webhook_parser.verify_signature(b"test_body", "invalid_signature")
        assert result is False