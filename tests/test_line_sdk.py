import pytest
from unittest.mock import AsyncMock, patch
from src.shared.line_sdk.client import LineClient
from src.shared.line_sdk.webhook import WebhookHandler
from src.shared.line_sdk.models import (
    TextMessage, ImageMessage, MessageEvent,
    UserSource, TextSendMessage, ImageSendMessage
)
from src.shared.events.types import Event

class TestLineSDK:
    @pytest.fixture
    def line_client(self):
        """LINE 客戶端測試夾具"""
        return LineClient(
            channel_secret="test_secret",
            channel_access_token="test_token"
        )
        
    @pytest.fixture
    def webhook_handler(self):
        """Webhook 處理器測試夾具"""
        return WebhookHandler(channel_secret="test_secret")
        
    @pytest.mark.asyncio
    async def test_send_text_message(self, line_client):
        """測試發送文本消息"""
        with patch('linebot.AsyncLineBotApi.push_message', new_callable=AsyncMock) as mock_push:
            await line_client.send_text(
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
        """測試發送圖片消息"""
        with patch('linebot.AsyncLineBotApi.push_message', new_callable=AsyncMock) as mock_push:
            await line_client.send_image(
                user_id="test_user",
                image_url="https://example.com/image.jpg",
                preview_url="https://example.com/preview.jpg"
            )
            
            mock_push.assert_called_once()
            args = mock_push.call_args[0]
            assert args[0] == "test_user"
            assert isinstance(args[1], ImageSendMessage)
            
    @pytest.mark.asyncio
    async def test_handle_text_message(self, webhook_handler):
        """測試處理文本消息"""
        # 模擬文本消息事件
        event = MessageEvent(
            message=TextMessage(text="Hello"),
            source=UserSource(user_id="test_user")
        )
        
        # 模擬事件處理器
        async def message_handler(event: Event):
            assert event.type == "message"
            assert event.data["content"] == "Hello"
            assert event.data["user_id"] == "test_user"
            
        webhook_handler.add_handler("message", message_handler)
        await webhook_handler.handle(event)
        
    @pytest.mark.asyncio
    async def test_handle_image_message(self, webhook_handler):
        """測試處理圖片消息"""
        # 模擬圖片消息事件
        event = MessageEvent(
            message=ImageMessage(id="test_image"),
            source=UserSource(user_id="test_user")
        )
        
        # 模擬圖片處理器
        async def image_handler(event: Event):
            assert event.type == "message"
            assert event.data["message_type"] == "image"
            assert event.data["user_id"] == "test_user"
            
        webhook_handler.add_handler("message", image_handler)
        await webhook_handler.handle(event)
        
    @pytest.mark.asyncio
    async def test_error_handling(self, line_client):
        """測試錯誤處理"""
        with patch('linebot.AsyncLineBotApi.push_message', new_callable=AsyncMock) as mock_push:
            mock_push.side_effect = Exception("API Error")
            
            with pytest.raises(Exception) as exc_info:
                await line_client.send_text(
                    user_id="test_user",
                    text="Should fail"
                )
                
            assert str(exc_info.value) == "API Error"
            
    @pytest.mark.asyncio
    async def test_webhook_signature_validation(self, webhook_handler):
        """測試 Webhook 簽名驗證"""
        # 模擬請求頭和消息體
        signature = "1234567890"
        body = b'{"events":[{"type":"message"}]}'
        
        with patch('linebot.WebhookHandler.verify_signature') as mock_verify:
            mock_verify.return_value = True
            assert webhook_handler.verify_signature(signature, body)
            
            mock_verify.return_value = False
            assert not webhook_handler.verify_signature(signature, body)
            
    @pytest.mark.asyncio
    async def test_message_reply(self, line_client):
        """測試消息回覆"""
        with patch('linebot.AsyncLineBotApi.reply_message', new_callable=AsyncMock) as mock_reply:
            await line_client.reply(
                reply_token="reply_token",
                text="Reply message"
            )
            
            mock_reply.assert_called_once()
            args = mock_reply.call_args[0]
            assert args[0] == "reply_token"
            assert isinstance(args[1], TextSendMessage)
            
    @pytest.mark.asyncio
    async def test_multiple_messages(self, line_client):
        """測試發送多條消息"""
        with patch('linebot.AsyncLineBotApi.push_message', new_callable=AsyncMock) as mock_push:
            messages = [
                TextSendMessage(text="Message 1"),
                TextSendMessage(text="Message 2")
            ]
            await line_client.push_messages(
                user_id="test_user",
                messages=messages
            )
            
            mock_push.assert_called_once()
            args = mock_push.call_args[0]
            assert args[0] == "test_user"
            assert len(args[1]) == 2
            
    @pytest.mark.asyncio
    async def test_user_profile(self, line_client):
        """測試獲取用戶資料"""
        mock_profile = {
            "userId": "test_user",
            "displayName": "Test User",
            "language": "zh-TW"
        }
        
        with patch('linebot.AsyncLineBotApi.get_profile', new_callable=AsyncMock) as mock_get:
            mock_get.return_value = mock_profile
            profile = await line_client.get_user_profile("test_user")
            
            assert profile["userId"] == "test_user"
            assert profile["displayName"] == "Test User"
            
    @pytest.mark.asyncio
    async def test_event_source_validation(self, webhook_handler):
        """測試事件來源驗證"""
        # 模擬無效的事件來源
        event = MessageEvent(
            message=TextMessage(text="Hello"),
            source=UserSource(user_id=None)  # 無效的用戶ID
        )
        
        with pytest.raises(ValueError):
            await webhook_handler.handle(event)
            
    @pytest.mark.asyncio
    async def test_rate_limit_handling(self, line_client):
        """測試速率限制處理"""
        with patch('linebot.AsyncLineBotApi.push_message', new_callable=AsyncMock) as mock_push:
            # 模擬速率限制錯誤
            mock_push.side_effect = Exception("Rate limit exceeded")
            
            with pytest.raises(Exception) as exc_info:
                await line_client.send_text(
                    user_id="test_user",
                    text="Should fail"
                )
                
            assert "Rate limit" in str(exc_info.value) 