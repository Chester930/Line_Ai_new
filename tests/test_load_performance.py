import pytest
import asyncio
import time
from unittest.mock import AsyncMock, patch
from src.shared.ai.models.gemini import GeminiModel
from src.shared.line_sdk.client import LineClient
from src.shared.database.base import Database
from src.shared.config.base import ConfigManager
from src.shared.utils.logger import logger

class TestLoadPerformance:
    @pytest.fixture
    async def setup(self):
        """設置測試環境"""
        config = ConfigManager()
        config.set("GOOGLE_API_KEY", "test_api_key")
        config.set("LINE_CHANNEL_SECRET", "test_secret")
        config.set("LINE_CHANNEL_ACCESS_TOKEN", "test_token")
        
        model = GeminiModel(config)
        client = LineClient(
            channel_secret=config.get("LINE_CHANNEL_SECRET"),
            channel_access_token=config.get("LINE_CHANNEL_ACCESS_TOKEN")
        )
        db = Database("sqlite+aiosqlite:///:memory:")
        
        return {
            "model": model,
            "client": client,
            "db": db
        }
        
    @pytest.mark.asyncio
    async def test_high_concurrency(self, setup):
        """測試高並發處理"""
        model = setup["model"]
        client = setup["client"]
        
        # 監控指標
        request_count = 0
        error_count = 0
        response_times = []
        
        async def process_request(user_id: str):
            nonlocal request_count, error_count
            start_time = time.time()
            
            try:
                with patch('google.generativeai.GenerativeModel.generate_content', new_callable=AsyncMock) as mock_generate:
                    mock_generate.return_value.text = f"Response to {user_id}"
                    response = await model.generate_text(f"Message from {user_id}")
                    
                    with patch('linebot.AsyncLineBotApi.push_message', new_callable=AsyncMock):
                        await client.send_text(user_id, response)
                        
                request_count += 1
                response_times.append(time.time() - start_time)
            except Exception as e:
                error_count += 1
                logger.error(f"Error in request: {str(e)}")
                
        # 模擬1000個並發請求
        users = [f"user_{i}" for i in range(1000)]
        tasks = [process_request(user_id) for user_id in users]
        
        start_time = time.time()
        await asyncio.gather(*tasks)
        total_time = time.time() - start_time
        
        # 計算性能指標
        avg_response_time = sum(response_times) / len(response_times)
        error_rate = error_count / request_count if request_count > 0 else 1
        
        # 驗證性能要求
        assert error_rate < 0.01  # 錯誤率小於1%
        assert avg_response_time < 1.0  # 平均響應時間小於1秒
        assert total_time < 30.0  # 總處理時間小於30秒
        
    @pytest.mark.asyncio
    async def test_resource_limits(self, setup):
        """測試資源限制"""
        model = setup["model"]
        
        # 監控記憶體使用
        import psutil
        process = psutil.Process()
        initial_memory = process.memory_info().rss
        
        # 生成大量回應
        with patch('google.generativeai.GenerativeModel.generate_content', new_callable=AsyncMock) as mock_generate:
            mock_generate.return_value.text = "Test response" * 100  # 大量文本
            
            responses = []
            for _ in range(100):
                response = await model.generate_text("Test message")
                responses.append(response)
                
        final_memory = process.memory_info().rss
        memory_increase = final_memory - initial_memory
        
        # 驗證資源使用限制
        assert memory_increase < 100 * 1024 * 1024  # 記憶體增加不超過100MB
        assert len(responses) == 100
        
    @pytest.mark.asyncio
    async def test_database_stress(self, setup):
        """測試數據庫壓力"""
        db = setup["db"]
        
        # 創建測試表
        async with db.session() as session:
            await session.execute("""
                CREATE TABLE test_load (
                    id INTEGER PRIMARY KEY,
                    data TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            await session.commit()
            
        async def db_operation(i: int):
            async with db.session() as session:
                # 插入
                await session.execute(
                    "INSERT INTO test_load (data) VALUES (:data)",
                    {"data": f"data_{i}"}
                )
                # 查詢
                await session.execute(
                    "SELECT * FROM test_load WHERE data = :data",
                    {"data": f"data_{i}"}
                )
                # 更新
                await session.execute(
                    "UPDATE test_load SET data = :new_data WHERE data = :old_data",
                    {"new_data": f"updated_{i}", "old_data": f"data_{i}"}
                )
                await session.commit()
                
        # 執行1000個並發數據庫操作
        tasks = [db_operation(i) for i in range(1000)]
        
        start_time = time.time()
        await asyncio.gather(*tasks)
        total_time = time.time() - start_time
        
        # 驗證數據庫性能
        assert total_time < 20.0  # 所有操作應在20秒內完成
        
    @pytest.mark.asyncio
    async def test_network_latency(self, setup):
        """測試網絡延遲"""
        client = setup["client"]
        
        async def send_message(delay: float):
            # 模擬網絡延遲
            await asyncio.sleep(delay)
            
            with patch('linebot.AsyncLineBotApi.push_message', new_callable=AsyncMock) as mock_push:
                start_time = time.time()
                await client.send_text("test_user", "Test message")
                return time.time() - start_time
                
        # 使用不同的延遲測試
        delays = [0.1, 0.2, 0.3, 0.4, 0.5]  # 模擬不同的網絡條件
        tasks = [send_message(delay) for delay in delays]
        
        response_times = await asyncio.gather(*tasks)
        
        # 驗證延遲處理
        for actual_time, expected_delay in zip(response_times, delays):
            assert abs(actual_time - expected_delay) < 0.1  # 允許0.1秒的誤差 