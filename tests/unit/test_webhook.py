import pytest
from unittest.mock import Mock, patch, AsyncMock
from fastapi import Request
from linebot.v3.webhooks import (
    MessageEvent,
    TextMessageContent,
    Source,
)
from src.shared.line_sdk.webhook import LineWebhookHandler, MessageHandler
from src.shared.line_sdk.client import line_client

@pytest.fixture
def webhook_handler():
    return LineWebhookHandler()

@pytest.fixture
def message_handler():
    return MessageHandler()

@pytest.fixture
def mock_request():
    request = AsyncMock(spec=Request)
    request.headers = {"X-Line-Signature": "test_signature"}
    request.body = AsyncMock(return_value=b"test_body")
    return request

@pytest.fixture
def mock_event():
    event = Mock(spec=MessageEvent)
    event.message = Mock(spec=TextMessageContent)
    return event

def test_webhook_handler_registration(webhook_handler):
    """測試處理器註冊"""
    @webhook_handler.add(MessageEvent)
    def handle_message(event):
        return "handled"
    
    assert MessageEvent in webhook_handler._handlers
    assert webhook_handler._handlers[MessageEvent](Mock()) == "handled"

def test_message_handler_registration(message_handler):
    """測試消息處理器註冊"""
    @message_handler.add(TextMessageContent)
    def handle_text(event):
        return "text_handled"
    
    assert (MessageEvent, TextMessageContent) in message_handler._handlers
    assert message_handler._handlers[(MessageEvent, TextMessageContent)](Mock()) == "text_handled"

@pytest.mark.asyncio
async def test_webhook_handler_handle_request(webhook_handler, mock_request, mock_event):
    """測試處理 webhook 請求"""
    @webhook_handler.add(MessageEvent)
    def handle_message(event):
        return "handled"
    
    with patch('src.shared.line_sdk.client.line_client.verify_webhook', return_value=True), \
         patch('src.shared.line_sdk.client.line_client.parse_webhook_body', return_value=[mock_event]):
        results = await webhook_handler.handle_request(mock_request)
        assert results == ["handled"]

def test_message_handler_handle_event(message_handler, mock_event):
    """測試處理消息事件"""
    @message_handler.add(TextMessageContent)
    def handle_text(event):
        return "text_handled"
    
    result = message_handler.handle_event(mock_event)
    assert result == "text_handled"

@pytest.mark.asyncio
async def test_webhook_handler_error_handling(webhook_handler, mock_request):
    """測試錯誤處理"""
    with patch('src.shared.line_sdk.client.line_client.verify_webhook', return_value=False):
        with pytest.raises(Exception, match="無效的 webhook 簽名"):
            await webhook_handler.handle_request(mock_request)

def test_message_handler_unknown_message_type(message_handler, mock_event):
    """測試未知消息類型"""
    mock_event.message = Mock(spec=object)  # 使用未註冊的消息類型
    result = message_handler.handle_event(mock_event)
    assert result is None 