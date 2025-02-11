import pytest
from unittest.mock import Mock, patch, AsyncMock
from linebot.v3.messaging import MessagingApi
from linebot.v3.webhook import WebhookParser
from linebot.v3.messaging.exceptions import ApiException
from src.shared.line_sdk.client import LineClient
from src.shared.line_sdk.webhook import WebhookParser
from src.shared.exceptions import ValidationError
import json

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
    with patch('src.shared.config.config.settings') as mock_settings:
        mock_settings.LINE_CHANNEL_ACCESS_TOKEN = "test_token"
        mock_settings.LINE_CHANNEL_SECRET = "test_secret"
        client = LineClient()
        return client

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
    with patch('src.shared.config.config.settings') as mock_settings:
        mock_settings.LINE_CHANNEL_ACCESS_TOKEN = "test_token"
        mock_settings.LINE_CHANNEL_SECRET = "test_secret"
        client = LineClient()
        
        # 測試發送文字消息
        with patch.object(client.messaging_api, 'push_message', AsyncMock()) as mock_push:
            mock_response = AsyncMock()
            mock_response.status = 200
            mock_push.return_value = mock_response
            
            response = await client.send_message("user_id", "test message")
            assert response.status == 200
            
            # 驗證請求
            mock_push.assert_called_once()

@pytest.mark.asyncio
async def test_line_client_error_handling():
    """測試 LINE 客戶端錯誤處理"""
    with patch('src.shared.config.config.settings') as mock_settings:
        mock_settings.LINE_CHANNEL_ACCESS_TOKEN = "test_token"
        mock_settings.LINE_CHANNEL_SECRET = "test_secret"
        client = LineClient()
        
        # 測試網絡錯誤
        with patch.object(client.messaging_api, 'push_message', AsyncMock(side_effect=Exception("Network error"))) as mock_push:
            with pytest.raises(Exception):
                await client.send_message("user_id", "test message")
        
        # 測試 API 錯誤響應
        with patch.object(client.messaging_api, 'push_message', AsyncMock(side_effect=ApiException(http_resp=Mock(status=400)))) as mock_push:
            with pytest.raises(ApiException):
                await client.send_message("user_id", "test message")

@pytest.mark.asyncio
async def test_line_client_message_types():
    """測試不同類型的消息發送"""
    with patch('src.shared.config.config.settings') as mock_settings:
        mock_settings.LINE_CHANNEL_ACCESS_TOKEN = "test_token"
        mock_settings.LINE_CHANNEL_SECRET = "test_secret"
        client = LineClient()
        
        with patch.object(client.messaging_api, 'push_message', AsyncMock()) as mock_push:
            mock_response = AsyncMock()
            mock_response.status = 200
            mock_push.return_value = mock_response
            
            # 測試發送貼圖消息
            response = await client.send_sticker_message(
                "user_id",
                package_id="1",
                sticker_id="1"
            )
            assert response.status == 200
            mock_push.assert_called_once()

@pytest.mark.asyncio
async def test_line_client_validation():
    """測試輸入驗證"""
    with patch('src.shared.config.config.settings') as mock_settings:
        mock_settings.LINE_CHANNEL_ACCESS_TOKEN = "test_token"
        mock_settings.LINE_CHANNEL_SECRET = "test_secret"
        client = LineClient()
        
        # 測試無效的用戶 ID
        with pytest.raises(ValueError):
            await client.send_message("", "test message")
        
        # 測試無效的消息內容
        with pytest.raises(ValueError):
            await client.send_message("user_id", "")

@pytest.mark.asyncio
async def test_line_client_batch_operations():
    """測試批量操作"""
    with patch('src.shared.config.config.settings') as mock_settings:
        mock_settings.LINE_CHANNEL_ACCESS_TOKEN = "test_token"
        mock_settings.LINE_CHANNEL_SECRET = "test_secret"
        client = LineClient()
        
        with patch.object(client.messaging_api, 'push_message', AsyncMock()) as mock_push:
            mock_response = AsyncMock()
            mock_response.status = 200
            mock_push.return_value = mock_response
            
            messages = [
                {"type": "text", "text": "message 1"},
                {"type": "text", "text": "message 2"}
            ]
            response = await client.send_messages("user_id", messages)
            assert response.status == 200
            mock_push.assert_called_once()

@pytest.mark.asyncio
async def test_line_client_rich_menu():
    """測試 Rich Menu 相關操作"""
    with patch('src.shared.config.config.settings') as mock_settings:
        mock_settings.LINE_CHANNEL_ACCESS_TOKEN = "test_token"
        mock_settings.LINE_CHANNEL_SECRET = "test_secret"
        client = LineClient()
        
        with patch.object(client.messaging_api, 'create_rich_menu', AsyncMock()) as mock_create:
            mock_response = AsyncMock()
            mock_response.status = 200
            mock_create.return_value = mock_response
            
            rich_menu_data = {
                "size": {"width": 2500, "height": 1686},
                "selected": False,
                "name": "Test Menu",
                "chatBarText": "Tap to open",
                "areas": []
            }
            
            response = await client.create_rich_menu(rich_menu_data)
            assert response.status == 200
            mock_create.assert_called_once_with(rich_menu_data)

@pytest.mark.asyncio
async def test_line_client_profile():
    """測試獲取用戶資料"""
    with patch('src.shared.config.config.settings') as mock_settings:
        mock_settings.LINE_CHANNEL_ACCESS_TOKEN = "test_token"
        mock_settings.LINE_CHANNEL_SECRET = "test_secret"
        client = LineClient()
        
        mock_profile = Mock()
        mock_profile.user_id = "test_user"
        mock_profile.display_name = "Test User"
        mock_profile.picture_url = "https://example.com/picture.jpg"
        mock_profile.status_message = "Test Status"
        
        with patch.object(client.messaging_api, 'get_profile', AsyncMock(return_value=mock_profile)) as mock_get:
            profile = await client.get_profile("test_user")
            assert profile["user_id"] == "test_user"
            assert profile["display_name"] == "Test User"
            mock_get.assert_called_once_with("test_user")

@pytest.mark.asyncio
async def test_line_client_group():
    """測試群組相關操作"""
    with patch('src.shared.config.config.settings') as mock_settings:
        mock_settings.LINE_CHANNEL_ACCESS_TOKEN = "test_token"
        mock_settings.LINE_CHANNEL_SECRET = "test_secret"
        client = LineClient()
        
        mock_group = Mock()
        mock_group.group_id = "test_group"
        mock_group.group_name = "Test Group"
        mock_group.picture_url = "https://example.com/group.jpg"
        
        with patch.object(client.messaging_api, 'get_group_summary', AsyncMock(return_value=mock_group)) as mock_get:
            response = await client.get_group_summary("test_group")
            assert response.group_id == "test_group"
            assert response.group_name == "Test Group"
            mock_get.assert_called_once_with("test_group")

@pytest.mark.asyncio
async def test_line_client_webhook():
    """測試 Webhook 相關功能"""
    with patch('src.shared.config.config.settings') as mock_settings:
        mock_settings.LINE_CHANNEL_ACCESS_TOKEN = "test_token"
        mock_settings.LINE_CHANNEL_SECRET = "test_secret"
        client = LineClient()
        
        with patch.object(client.messaging_api, 'set_webhook_endpoint', AsyncMock()) as mock_set:
            mock_response = AsyncMock()
            mock_response.status = 200
            mock_set.return_value = mock_response
            
            webhook_url = "https://example.com/webhook"
            response = await client.set_webhook_url(webhook_url)
            assert response.status == 200
            mock_set.assert_called_once()

@pytest.mark.asyncio
async def test_line_client_quota():
    """測試配額相關功能"""
    with patch('src.shared.config.config.settings') as mock_settings:
        mock_settings.LINE_CHANNEL_ACCESS_TOKEN = "test_token"
        mock_settings.LINE_CHANNEL_SECRET = "test_secret"
        client = LineClient()
        
        mock_quota = Mock()
        mock_quota.type = "limited"
        mock_quota.value = 1000
        
        with patch.object(client.messaging_api, 'get_message_quota', AsyncMock(return_value=mock_quota)) as mock_get:
            response = await client.get_message_quota()
            assert response.type == "limited"
            assert response.value == 1000
            mock_get.assert_called_once()

@pytest.mark.asyncio
async def test_line_client_multicast():
    """測試多人發送功能"""
    with patch('src.shared.config.config.settings') as mock_settings:
        mock_settings.LINE_CHANNEL_ACCESS_TOKEN = "test_token"
        mock_settings.LINE_CHANNEL_SECRET = "test_secret"
        client = LineClient()
        
        with patch.object(client.messaging_api, 'multicast', AsyncMock()) as mock_multicast:
            mock_response = AsyncMock()
            mock_response.status = 200
            mock_multicast.return_value = mock_response
            
            user_ids = ["user1", "user2", "user3"]
            message = {"type": "text", "text": "Hello everyone!"}
            
            response = await client.multicast(user_ids, [message])
            assert response.status == 200
            mock_multicast.assert_called_once()

@pytest.mark.asyncio
async def test_line_client_content():
    """測試內容相關功能"""
    with patch('src.shared.config.config.settings') as mock_settings:
        mock_settings.LINE_CHANNEL_ACCESS_TOKEN = "test_token"
        mock_settings.LINE_CHANNEL_SECRET = "test_secret"
        client = LineClient()
        
        # 測試獲取訊息內容
        mock_content = AsyncMock()
        mock_content.status = 200
        mock_content.read = AsyncMock(return_value=b"test content")
        
        with patch.object(client.messaging_api, 'get_message_content', AsyncMock(return_value=mock_content)) as mock_get:
            message_id = "test_message_id"
            response = await client.get_content(message_id)
            assert response.status == 200
            
            content = await response.read()
            assert content == b"test content"
            mock_get.assert_called_once_with(message_id)