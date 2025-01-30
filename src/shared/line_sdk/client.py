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
        await self.messaging_api.push_message(user_id, message)

    async def reply_message(self, reply_token: str, message: str):
        """回覆消息"""
        await self.messaging_api.reply_message(reply_token, message)

    async def get_profile(self, user_id: str) -> dict:
        """獲取用戶資料
        
        Args:
            user_id: 用戶 ID
            
        Returns:
            用戶資料字典
        """
        profile = await self.messaging_api.get_profile(user_id)
        return {
            'user_id': profile.user_id,
            'display_name': profile.display_name,
            'picture_url': profile.picture_url,
            'status_message': profile.status_message
        }

# 創建全局客戶端實例
line_client = LineClient() 