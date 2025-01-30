import pytest
from unittest.mock import Mock, patch, AsyncMock
from fastapi import Request
from linebot.v3.webhook import WebhookHandler
from linebot.models import (
    MessageEvent,
    TextMessage,
    TextSendMessage
)
from src.line.handler import LineBotHandler
from src.shared.config.config import settings
from src.shared.events.types import MessageEvent as AppMessageEvent

@pytest.fixture
def webhook_handler():
    """創建 LINE Bot 處理器實例"""
    return LineBotHandler()

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
        # 設置 mock 行為
        mock_publisher.publish = AsyncMock()
        
        # 確保處理器已初始化
        webhook_handler._setup_handlers()
        
        # 獲取處理函數
        handler_func = None
        for key, func in webhook_handler.handler._handlers.items():
            if key == MessageEvent:
                handler_func = func
                break
        
        assert handler_func is not None, "No handler found for MessageEvent with TextMessage"
        
        # 調用處理函數
        result = await handler_func(mock_event)
        
        # 驗證結果
        assert isinstance(result, TextSendMessage)
        assert result.text == "Hello, World!"
        
        # 驗證事件發布
        expected_event = AppMessageEvent(
            message_id="test_message_id",
            user_id="test_user_id",
            content="Hello, World!"
        )
        mock_publisher.publish.assert_awaited_once_with(expected_event)

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