import pytest
from unittest.mock import Mock, patch, AsyncMock
from fastapi import Request
from linebot.v3.webhooks import MessageEvent, TextMessageContent
from src.shared.line_sdk.webhook import LineWebhookHandler, MessageHandler

@pytest.fixture
def webhook_handler():
    return LineWebhookHandler()

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