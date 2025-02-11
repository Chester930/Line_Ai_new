import pytest
import asyncio
from unittest.mock import AsyncMock, patch
from src.shared.ai.models.gemini import GeminiModel
from src.shared.line_sdk.client import LineClient
from src.shared.database.base import Database
from src.shared.config.base import ConfigManager
from src.shared.events.base import EventEmitter

class TestEdgeCases:
    @pytest.fixture
    def config(self):
        config = ConfigManager()
        config.set("GOOGLE_API_KEY", "test_api_key")
        config.set("LINE_CHANNEL_SECRET", "test_secret")
        config.set("LINE_CHANNEL_ACCESS_TOKEN", "test_token")
        return config
        
    @pytest.mark.asyncio
    async def test_empty_input(self, config):
        """測試空輸入處理"""
        model = GeminiModel(config)
        
        with patch('google.generativeai.GenerativeModel.generate_content', new_callable=AsyncMock) as mock_generate:
            # 測試空字符串
            response = await model.generate_text("")
            assert response is not None
            assert len(response) > 0
            
            # 測試純空格
            response = await model.generate_text("   ")
            assert response is not None
            assert len(response) > 0
            
    @pytest.mark.asyncio
    async def test_large_input(self, config):
        """測試大量輸入"""
        model = GeminiModel(config)
        large_text = "test " * 1000  # 大約 5000 字符
        
        with patch('google.generativeai.GenerativeModel.generate_content', new_callable=AsyncMock) as mock_generate:
            mock_generate.return_value.text = "Response to large input"
            response = await model.generate_text(large_text)
            assert response is not None
            
    @pytest.mark.asyncio
    async def test_special_characters(self, config):
        """測試特殊字符"""
        model = GeminiModel(config)
        special_chars = "!@#$%^&*()_+-=[]{}|;:'\",.<>?/~`"
        
        with patch('google.generativeai.GenerativeModel.generate_content', new_callable=AsyncMock) as mock_generate:
            mock_generate.return_value.text = "Response with special chars"
            response = await model.generate_text(special_chars)
            assert response is not None
            
    @pytest.mark.asyncio
    async def test_concurrent_database_access(self, config):
        """測試並發數據庫訪問"""
        db = Database("sqlite+aiosqlite:///:memory:")
        
        async def concurrent_write(i: int):
            async with db.session() as session:
                await session.execute(
                    "INSERT INTO test (value) VALUES (:value)",
                    {"value": f"test_{i}"}
                )
                await session.commit()
                
        # 創建測試表
        async with db.session() as session:
            await session.execute("CREATE TABLE test (id INTEGER PRIMARY KEY, value TEXT)")
            await session.commit()
            
        # 並發寫入
        tasks = [concurrent_write(i) for i in range(100)]
        await asyncio.gather(*tasks)
        
        # 驗證數據完整性
        async with db.session() as session:
            result = await session.execute("SELECT COUNT(*) FROM test")
            count = result.scalar()
            assert count == 100
            
    @pytest.mark.asyncio
    async def test_unicode_handling(self, config):
        """測試 Unicode 處理"""
        model = GeminiModel(config)
        unicode_text = "你好世界 🌍 こんにちは 안녕하세요"
        
        with patch('google.generativeai.GenerativeModel.generate_content', new_callable=AsyncMock) as mock_generate:
            mock_generate.return_value.text = "Unicode response"
            response = await model.generate_text(unicode_text)
            assert response is not None
            
    @pytest.mark.asyncio
    async def test_rate_limiting(self, config):
        """測試速率限制"""
        client = LineClient(
            channel_secret=config.get("LINE_CHANNEL_SECRET"),
            channel_access_token=config.get("LINE_CHANNEL_ACCESS_TOKEN")
        )
        
        # 快速發送多條消息
        messages = ["test"] * 5
        
        with patch('linebot.AsyncLineBotApi.push_message', new_callable=AsyncMock) as mock_push:
            tasks = [
                client.send_text("test_user", msg)
                for msg in messages
            ]
            await asyncio.gather(*tasks)
            
            assert mock_push.call_count == 5 