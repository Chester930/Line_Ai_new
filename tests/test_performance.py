import pytest
import asyncio
import time
from unittest.mock import AsyncMock, patch
from src.shared.ai.models.gemini import GeminiModel
from src.shared.line_sdk.client import LineClient
from src.shared.config.base import ConfigManager
from src.shared.database.base import Database
from src.shared.database.models.conversation import Conversation
from sqlalchemy import select

class TestPerformance:
    @pytest.fixture
    def config(self):
        """配置測試夾具"""
        config = ConfigManager()
        config.set("GOOGLE_API_KEY", "test_api_key")
        config.set("LINE_CHANNEL_SECRET", "test_secret")
        config.set("LINE_CHANNEL_ACCESS_TOKEN", "test_token")
        return config
        
    @pytest.mark.asyncio
    async def test_response_time(self, config):
        """測試響應時間"""
        model = GeminiModel(config)
        
        with patch('google.generativeai.GenerativeModel.generate_content', new_callable=AsyncMock) as mock_generate:
            mock_generate.return_value.text = "Test response"
            
            start_time = time.time()
            await model.generate_text("Test prompt")
            end_time = time.time()
            
            response_time = end_time - start_time
            assert response_time < 1.0  # 響應時間應小於1秒
            
    @pytest.mark.asyncio
    async def test_concurrent_requests(self, config):
        """測試並發請求"""
        model = GeminiModel(config)
        client = LineClient(
            channel_secret=config.get("LINE_CHANNEL_SECRET"),
            channel_access_token=config.get("LINE_CHANNEL_ACCESS_TOKEN")
        )
        
        async def process_request(user_id: str, message: str):
            with patch('google.generativeai.GenerativeModel.generate_content', new_callable=AsyncMock) as mock_generate:
                mock_generate.return_value.text = f"Response to {message}"
                response = await model.generate_text(message)
                
                with patch('linebot.AsyncLineBotApi.push_message', new_callable=AsyncMock) as mock_push:
                    await client.send_text(user_id, response)
                    return response
                    
        # 模擬10個並發請求
        requests = [
            process_request(f"user_{i}", f"Message {i}")
            for i in range(10)
        ]
        
        start_time = time.time()
        responses = await asyncio.gather(*requests)
        end_time = time.time()
        
        total_time = end_time - start_time
        assert len(responses) == 10
        assert total_time < 3.0  # 所有請求應在3秒內完成
        
    @pytest.mark.asyncio
    async def test_database_performance(self, config):
        """測試數據庫性能"""
        async with Database("sqlite+aiosqlite:///:memory:").session() as session:
            # 批量插入測試
            start_time = time.time()
            conversations = [
                Conversation(
                    user_id=1,
                    message=f"Message {i}",
                    role="user"
                )
                for i in range(100)
            ]
            session.add_all(conversations)
            await session.commit()
            end_time = time.time()
            
            insert_time = end_time - start_time
            assert insert_time < 1.0  # 批量插入應在1秒內完成
            
            # 批量查詢測試
            start_time = time.time()
            result = await session.execute(
                select(Conversation).where(Conversation.user_id == 1)
            )
            conversations = result.scalars().all()
            end_time = time.time()
            
            query_time = end_time - start_time
            assert query_time < 0.5  # 查詢應在0.5秒內完成
            assert len(conversations) == 100
            
    @pytest.mark.asyncio
    async def test_memory_usage(self, config):
        """測試記憶體使用"""
        import psutil
        import os
        
        process = psutil.Process(os.getpid())
        initial_memory = process.memory_info().rss
        
        # 執行密集操作
        model = GeminiModel(config)
        with patch('google.generativeai.GenerativeModel.generate_content', new_callable=AsyncMock) as mock_generate:
            mock_generate.return_value.text = "Test response"
            
            # 生成大量回應
            for _ in range(100):
                await model.generate_text("Test prompt")
                
        final_memory = process.memory_info().rss
        memory_increase = final_memory - initial_memory
        
        # 記憶體增加不應超過 50MB
        assert memory_increase < 50 * 1024 * 1024
        
    @pytest.mark.asyncio
    async def test_connection_pool(self, config):
        """測試連接池性能"""
        db = Database("sqlite+aiosqlite:///:memory:")
        
        async def db_operation():
            async with db.session() as session:
                await session.execute("SELECT 1")
                await session.commit()
                
        # 模擬多個並發數據庫操作
        tasks = [db_operation() for _ in range(20)]
        
        start_time = time.time()
        await asyncio.gather(*tasks)
        end_time = time.time()
        
        total_time = end_time - start_time
        assert total_time < 2.0  # 所有操作應在2秒內完成 