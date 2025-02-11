import os
import logging
from typing import Optional, List, Union, Dict
from linebot.v3.messaging import (
    MessagingApi,
    ApiClient,
    Configuration,
    PushMessageRequest,
    TextMessage
)
from linebot.v3.webhook import WebhookParser
from linebot.models import (
    TextSendMessage,
    ImageSendMessage,
    TemplateSendMessage,
    ButtonsTemplate,
    MessageAction,
)
from linebot.exceptions import LineBotApiError
from src.shared.config.config import Config
from ..config.config import config
from ..utils.logger import logger

logger = logging.getLogger(__name__)

class LineClient:
    """LINE API 客戶端"""
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self):
        if not hasattr(self, 'initialized'):
            self.channel_secret = config.settings.line_channel_secret
            self.channel_access_token = config.settings.line_channel_access_token
            self.messaging_api = MessagingApi(self.channel_access_token)
            self.parser = WebhookParser(self.channel_secret)
            self.initialized = True
    
    def verify_webhook(self, body: bytes, signature: str) -> bool:
        """驗證 webhook 簽名"""
        try:
            return self.parser.signature_validator.validate(body, signature)
        except Exception as e:
            logger.error(f"驗證 webhook 簽名失敗: {str(e)}")
            return False
    
    def parse_webhook_body(self, body: bytes):
        """解析 webhook 請求體"""
        return self.parser.parse(body)

    async def send_message(self, user_id: str, message: str):
        """發送消息"""
        if not user_id:
            raise ValueError("用戶 ID 不能為空")
        if not message:
            raise ValueError("消息內容不能為空")
        
        message_request = PushMessageRequest(
            to=user_id,
            messages=[TextMessage(text=message)]
        )
        return await self.messaging_api.push_message(message_request)

    async def reply_message(self, reply_token: str, message: str):
        """回覆消息"""
        message_request = {
            "replyToken": reply_token,
            "messages": [
                {
                    "type": "text",
                    "text": message
                }
            ]
        }
        return await self.messaging_api.reply_message(message_request)

    async def get_profile(self, user_id: str) -> dict:
        """獲取用戶資料"""
        profile = await self.messaging_api.get_profile(user_id)
        return {
            'user_id': profile.user_id,
            'display_name': profile.display_name,
            'picture_url': profile.picture_url,
            'status_message': profile.status_message
        }

    async def send_sticker_message(self, user_id: str, package_id: str, sticker_id: str):
        """發送貼圖消息"""
        message_request = PushMessageRequest(
            to=user_id,
            messages=[{
                "type": "sticker",
                "packageId": package_id,
                "stickerId": sticker_id
            }]
        )
        return await self.messaging_api.push_message(message_request)

    async def send_messages(self, user_id: str, messages: list):
        """批量發送消息"""
        message_request = PushMessageRequest(
            to=user_id,
            messages=messages
        )
        return await self.messaging_api.push_message(message_request)

    async def create_rich_menu(self, rich_menu_data: dict):
        """創建 Rich Menu"""
        return await self.messaging_api.create_rich_menu(rich_menu_data)

    async def get_group_summary(self, group_id: str):
        """獲取群組資訊"""
        return await self.messaging_api.get_group_summary(group_id)

    async def set_webhook_url(self, webhook_url: str):
        """設置 Webhook URL"""
        request = {
            "endpoint": webhook_url
        }
        return await self.messaging_api.set_webhook_endpoint(request)

    async def get_message_quota(self):
        """獲取消息配額"""
        return await self.messaging_api.get_message_quota()

    async def multicast(self, user_ids: list, messages: list):
        """多人發送消息"""
        request = {
            "to": user_ids,
            "messages": [
                {
                    "type": "text",
                    "text": msg["text"] if isinstance(msg, dict) else msg
                } for msg in messages
            ]
        }
        return await self.messaging_api.multicast(request)

    async def get_content(self, message_id: str):
        """獲取消息內容"""
        return await self.messaging_api.get_message_content(message_id)

# 創建全局客戶端實例
line_client = LineClient() 