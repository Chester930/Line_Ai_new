from typing import Dict, Any
import aiohttp
import base64
from src.shared.plugins.base import BasePlugin, PluginConfig
from src.shared.utils.logger import logger

class ImageAnalyzerPlugin(BasePlugin):
    """圖片分析插件"""
    
    async def initialize(self) -> bool:
        """初始化插件"""
        try:
            self.api_key = self.get_setting("api_key")
            self.model = self.get_setting("model", "gemini-pro-vision")
            self.session = aiohttp.ClientSession()
            return True
        except Exception as e:
            logger.error(f"初始化圖片分析插件失敗: {str(e)}")
            return False
    
    async def execute(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """執行圖片分析"""
        try:
            image_data = context.get("image")
            prompt = context.get("prompt", "描述這張圖片")
            
            if not image_data:
                raise ValueError("圖片數據不能為空")
            
            # 如果是 URL，下載圖片
            if isinstance(image_data, str) and image_data.startswith("http"):
                async with self.session.get(image_data) as response:
                    image_data = await response.read()
            
            # 轉換為 base64
            if isinstance(image_data, bytes):
                image_data = base64.b64encode(image_data).decode()
            
            # 調用 AI 模型分析圖片
            async with self.session.post(
                "https://api.google.com/v1/models/gemini-pro-vision:predict",
                headers={"Authorization": f"Bearer {self.api_key}"},
                json={
                    "contents": [{
                        "parts": [
                            {"text": prompt},
                            {
                                "inline_data": {
                                    "mime_type": "image/jpeg",
                                    "data": image_data
                                }
                            }
                        ]
                    }]
                }
            ) as response:
                result = await response.json()
            
            return {
                "success": True,
                "description": result["candidates"][0]["content"]["parts"][0]["text"]
            }
            
        except Exception as e:
            logger.error(f"執行圖片分析失敗: {str(e)}")
            return {
                "success": False,
                "error": str(e)
            }
    
    async def cleanup(self) -> None:
        """清理資源"""
        if hasattr(self, "session"):
            await self.session.close() 