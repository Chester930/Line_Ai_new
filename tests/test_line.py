import pytest
from unittest.mock import Mock, patch, AsyncMock
from src.shared.line_sdk.client import LineClient
from src.shared.line_sdk.webhook import WebhookHandler
from linebot.models import (
    MessageEvent, TextMessage, TextSendMessage,
    ImageMessage, ImageSendMessage
)

class TestLineClient:
    @pytest.fixture
    def line_client(self):
        return LineClient(
            channel_secret="test_secret",
            channel_access_token="test_token"
        )
    
    @pytest.mark.asyncio
    async def test_send_text_message(self, line_client):
        with patch('linebot.AsyncLineBotApi.push_message', new_callable=AsyncMock) as mock_push:
            await line_client.send_text_message(
                user_id="test_user",
                text="Hello, World!"
            )
            mock_push.assert_called_once()
            args = mock_push.call_args[0]
            assert args[0] == "test_user"
            assert isinstance(args[1], TextSendMessage)
            assert args[1].text == "Hello, World!"
            
    @pytest.mark.asyncio
    async def test_send_image_message(self, line_client):
        with patch('linebot.AsyncLineBotApi.push_message', new_callable=AsyncMock) as mock_push:
            await line_client.send_image_message(
                user_id="test_user",
                image_url="https://example.com/image.jpg",
                preview_url="https://example.com/preview.jpg"
            )
            mock_push.assert_called_once()
            args = mock_push.call_args[0]
            assert args[0] == "test_user"
            assert isinstance(args[1], ImageSendMessage)
            
    @pytest.mark.asyncio
    async def test_error_handling(self, line_client):
        with patch('linebot.AsyncLineBotApi.push_message', new_callable=AsyncMock) as mock_push:
            mock_push.side_effect = Exception("API Error")
            with pytest.raises(Exception):
                await line_client.send_text_message(
                    user_id="test_user",
                    text="Should fail"
                )

class TestWebhookHandler:
    @pytest.fixture
    def webhook_handler(self):
        return WebhookHandler(channel_secret="test_secret")
    
    @pytest.mark.asyncio
    async def test_handle_text_message(self, webhook_handler):
        # 模擬文本消息事件
        event = MessageEvent(
            message=TextMessage(text="Hello"),
            source={"type": "user", "userId": "test_user"}
        )
        
        with patch.object(webhook_handler, '_handle_text_message', new_callable=AsyncMock) as mock_handle:
            await webhook_handler.handle_event(event)
            mock_handle.assert_called_once_with(event)
            
    @pytest.mark.asyncio
    async def test_handle_image_message(self, webhook_handler):
        # 模擬圖片消息事件
        event = MessageEvent(
            message=ImageMessage(id="test_image"),
            source={"type": "user", "userId": "test_user"}
        )
        
        with patch.object(webhook_handler, '_handle_image_message', new_callable=AsyncMock) as mock_handle:
            await webhook_handler.handle_event(event)
            mock_handle.assert_called_once_with(event) 