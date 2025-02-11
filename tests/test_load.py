import pytest
import asyncio
import time
from unittest.mock import AsyncMock, patch
from src.shared.ai.models.gemini import GeminiModel
from src.shared.line_sdk.client import LineClient
from src.shared.config.base import ConfigManager
from src.shared.database.base import Database
from src.shared.events.base import EventEmitter

class TestLoad:
    @pytest.fixture
    def config(self):
        config = ConfigManager()
        config.set("GOOGLE_API_KEY", "test_api_key")
        config.set("LINE_CHANNEL_SECRET", "test_secret")
        config.set("LINE_CHANNEL_ACCESS_TOKEN", "test_token")
        return config
        
    @pytest.mark.asyncio
    async def test_high_concurrency(self, config):
        """測試高並發處理"""
        model = GeminiModel(config)
        client = LineClient(
            channel_secret=config.get("LINE_CHANNEL_SECRET"),
            channel_access_token=config.get("LINE_CHANNEL_ACCESS_TOKEN")
        )
        
        # 模擬大量並發請求
        async def process_request(user_id: str):
            with patch('google.generativeai.GenerativeModel.generate_content', new_callable=AsyncMock) as mock_generate:
                mock_generate.return_value.text = f"Response to user {user_id}"
                response = await model.generate_text(f"Message from {user_id}")
                
                with patch('linebot.AsyncLineBotApi.push_message', new_callable=AsyncMock) as mock_push:
                    await client.send_text(user_id, response)
                    return response
                    
        # 模擬100個並發用戶
        tasks = [process_request(f"user_{i}") for i in range(100)]
        
        start_time = time.time()
        responses = await asyncio.gather(*tasks)
        end_time = time.time()
        
        total_time = end_time - start_time
        assert len(responses) == 100
        assert total_time < 10.0  # 100個請求應在10秒內完成
        
    @pytest.mark.asyncio
    async def test_sustained_load(self, config):
        """測試持續負載"""
        model = GeminiModel(config)
        event_emitter = EventEmitter()
        
        # 監控指標
        request_count = 0
        error_count = 0
        total_response_time = 0
        
        async def load_test(duration_seconds: int = 60):
            nonlocal request_count, error_count, total_response_time
            end_time = time.time() + duration_seconds
            
            while time.time() < end_time:
                start = time.time()
                try:
                    with patch('google.generativeai.GenerativeModel.generate_content', new_callable=AsyncMock) as mock_generate:
                        mock_generate.return_value.text = "Test response"
                        await model.generate_text("Test message")
                        request_count += 1
                        total_response_time += time.time() - start
                except Exception:
                    error_count += 1
                    
                await asyncio.sleep(0.1)  # 模擬請求間隔
                
        await load_test(10)  # 運行10秒測試
        
        avg_response_time = total_response_time / request_count if request_count > 0 else 0
        error_rate = error_count / request_count if request_count > 0 else 0
        
        assert request_count > 0
        assert error_rate < 0.01  # 錯誤率應小於1%
        assert avg_response_time < 0.5  # 平均響應時間應小於0.5秒
        
    @pytest.mark.asyncio
    async def test_database_load(self, config):
        """測試數據庫負載"""
        db = Database("sqlite+aiosqlite:///:memory:")
        
        async def db_write():
            async with db.session() as session:
                for i in range(100):
                    await session.execute(
                        "INSERT INTO test_table (value) VALUES (:value)",
                        {"value": f"test_{i}"}
                    )
                await session.commit()
                
        async def db_read():
            async with db.session() as session:
                for _ in range(100):
                    await session.execute("SELECT * FROM test_table")
                    
        # 創建測試表
        async with db.session() as session:
            await session.execute(
                "CREATE TABLE test_table (id INTEGER PRIMARY KEY, value TEXT)"
            )
            await session.commit()
            
        # 並發讀寫測試
        tasks = [db_write(), db_read()]
        start_time = time.time()
        await asyncio.gather(*tasks)
        end_time = time.time()
        
        total_time = end_time - start_time
        assert total_time < 5.0  # 所有操作應在5秒內完成
        
    @pytest.mark.asyncio
    async def test_event_system_load(self, config):
        """測試事件系統負載"""
        emitter = EventEmitter()
        received_events = []
        
        async def event_handler(event):
            received_events.append(event)
            await asyncio.sleep(0.01)  # 模擬處理時間
            
        # 註冊事件處理器
        emitter.on("test_event", event_handler)
        
        # 發送大量事件
        events = [
            {"type": "test_event", "data": {"id": i}}
            for i in range(1000)
        ]
        
        start_time = time.time()
        await asyncio.gather(*[
            emitter.emit(event)
            for event in events
        ])
        end_time = time.time()
        
        total_time = end_time - start_time
        assert len(received_events) == 1000
        assert total_time < 15.0  # 處理1000個事件應在15秒內完成 