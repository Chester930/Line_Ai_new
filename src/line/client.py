from typing import Optional, List
from linebot import LineBotApi
from linebot.models import (
    TextSendMessage,
    ImageSendMessage,
    TemplateSendMessage
)
from ..shared.config.manager import config_manager
from ..shared.utils.logger import logger

class LineBotClient:
    """LINE Bot API 客戶端"""
    
    def __init__(self):
        config = config_manager.get_line_config()
        self.client = LineBotApi(config.get("channel_access_token"))
    
    async def send_text(
        self,
        user_id: str,
        text: str
    ) -> bool:
        """發送文字消息"""
        try:
            await self.client.push_message(
                user_id,
                TextSendMessage(text=text)
            )
            return True
        except Exception as e:
            logger.error(f"發送文字消息失敗: {str(e)}")
            return False
    
    async def send_image(
        self,
        user_id: str,
        image_url: str,
        preview_url: Optional[str] = None
    ) -> bool:
        """發送圖片消息"""
        try:
            await self.client.push_message(
                user_id,
                ImageSendMessage(
                    original_content_url=image_url,
                    preview_image_url=preview_url or image_url
                )
            )
            return True
        except Exception as e:
            logger.error(f"發送圖片消息失敗: {str(e)}")
            return False
    
    async def get_profile(self, user_id: str) -> Optional[dict]:
        """獲取用戶資料"""
        try:
            profile = await self.client.get_profile(user_id)
            return {
                "user_id": profile.user_id,
                "display_name": profile.display_name,
                "picture_url": profile.picture_url,
                "status_message": profile.status_message
            }
        except Exception as e:
            logger.error(f"獲取用戶資料失敗: {str(e)}")
            return None

# 創建全局 LINE Bot 客戶端實例
line_client = LineBotClient() 