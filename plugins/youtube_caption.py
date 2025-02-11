from typing import Dict, Any
import yt_dlp
from src.shared.plugins.base import BasePlugin, PluginConfig
from src.shared.utils.logger import logger

class YouTubeCaptionPlugin(BasePlugin):
    """YouTube 字幕提取插件"""
    
    async def initialize(self) -> bool:
        """初始化插件"""
        try:
            self.language = self.get_setting("language", "zh-TW")
            self.ydl_opts = {
                'writesubtitles': True,
                'writeautomaticsub': True,
                'subtitleslangs': [self.language],
                'skip_download': True
            }
            return True
        except Exception as e:
            logger.error(f"初始化 YouTube 字幕插件失敗: {str(e)}")
            return False
    
    async def execute(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """提取字幕"""
        try:
            video_url = context.get("url")
            if not video_url:
                raise ValueError("視頻 URL 不能為空")
            
            # 提取字幕
            with yt_dlp.YoutubeDL(self.ydl_opts) as ydl:
                info = ydl.extract_info(video_url, download=False)
                
                # 獲取字幕
                subtitles = info.get('subtitles', {})
                auto_subs = info.get('automatic_captions', {})
                
                # 優先使用手動字幕，如果沒有則使用自動字幕
                captions = subtitles.get(self.language) or auto_subs.get(self.language)
                
                if not captions:
                    return {
                        "success": False,
                        "error": f"找不到 {self.language} 語言的字幕"
                    }
                
                # 獲取文本格式的字幕
                text_captions = next(
                    (c for c in captions if c['ext'] == 'txt'),
                    None
                )
                
                if not text_captions:
                    return {
                        "success": False,
                        "error": "找不到文本格式的字幕"
                    }
                
                return {
                    "success": True,
                    "title": info.get('title'),
                    "duration": info.get('duration'),
                    "captions": text_captions['url']
                }
                
        except Exception as e:
            logger.error(f"提取字幕失敗: {str(e)}")
            return {
                "success": False,
                "error": str(e)
            }
    
    async def cleanup(self) -> None:
        """清理資源"""
        pass 