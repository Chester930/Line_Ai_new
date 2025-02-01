from typing import Dict, Any
import aiohttp
from src.shared.plugins.base import BasePlugin, PluginConfig

class WebSearchPlugin(BasePlugin):
    """網頁搜索插件"""
    
    async def initialize(self) -> bool:
        """初始化插件"""
        try:
            self.api_key = self.get_setting("api_key")
            self.search_engine = self.get_setting("search_engine", "google")
            self.session = aiohttp.ClientSession()
            return True
        except Exception as e:
            logger.error(f"初始化網頁搜索插件失敗: {str(e)}")
            return False
    
    async def execute(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """執行搜索"""
        try:
            query = context.get("query")
            if not query:
                raise ValueError("搜索查詢不能為空")
                
            # 執行搜索
            async with self.session.get(
                f"https://api.{self.search_engine}.com/search",
                params={
                    "q": query,
                    "key": self.api_key
                }
            ) as response:
                results = await response.json()
                
            return {
                "success": True,
                "results": results
            }
            
        except Exception as e:
            logger.error(f"執行搜索失敗: {str(e)}")
            return {
                "success": False,
                "error": str(e)
            }
    
    async def cleanup(self) -> None:
        """清理資源"""
        if hasattr(self, "session"):
            await self.session.close() 