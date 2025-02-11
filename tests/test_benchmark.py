import pytest
import asyncio
import time
import statistics
from unittest.mock import AsyncMock, patch
from src.shared.ai.models.gemini import GeminiModel
from src.shared.line_sdk.client import LineClient
from src.shared.database.base import Database
from src.shared.config.base import ConfigManager

class TestBenchmark:
    @pytest.fixture
    def setup(self):
        """設置測試環境"""
        config = ConfigManager()
        config.set("GOOGLE_API_KEY", "test_api_key")
        config.set("LINE_CHANNEL_SECRET", "test_secret")
        config.set("LINE_CHANNEL_ACCESS_TOKEN", "test_token")
        return config
        
    @pytest.mark.benchmark
    @pytest.mark.asyncio
    async def test_ai_model_performance(self, setup):
        """AI 模型性能基準測試"""
        model = GeminiModel(setup)
        response_times = []
        
        with patch('google.generativeai.GenerativeModel.generate_content', new_callable=AsyncMock) as mock_generate:
            mock_generate.return_value.text = "Benchmark response"
            
            # 執行100次請求
            for _ in range(100):
                start_time = time.time()
                await model.generate_text("Benchmark test")
                response_times.append(time.time() - start_time)
                
        # 計算性能指標
        avg_time = statistics.mean(response_times)
        p95_time = statistics.quantiles(response_times, n=20)[18]  # 95th percentile
        p99_time = statistics.quantiles(response_times, n=100)[98]  # 99th percentile
        
        # 驗證性能要求
        assert avg_time < 0.1  # 平均響應時間 < 100ms
        assert p95_time < 0.2  # 95% 請求 < 200ms
        assert p99_time < 0.5  # 99% 請求 < 500ms
        
    @pytest.mark.benchmark
    @pytest.mark.asyncio
    async def test_database_performance(self, setup):
        """數據庫性能基準測試"""
        db = Database("sqlite+aiosqlite:///:memory:")
        query_times = []
        
        # 創建測試表
        async with db.session() as session:
            await session.execute("""
                CREATE TABLE benchmark (
                    id INTEGER PRIMARY KEY,
                    data TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            await session.commit()
            
            # 插入測試數據
            for i in range(1000):
                start_time = time.time()
                await session.execute(
                    "INSERT INTO benchmark (data) VALUES (:data)",
                    {"data": f"data_{i}"}
                )
                query_times.append(time.time() - start_time)
                
            await session.commit()
            
        # 計算性能指標
        avg_time = statistics.mean(query_times)
        max_time = max(query_times)
        
        # 驗證性能要求
        assert avg_time < 0.001  # 平均查詢時間 < 1ms
        assert max_time < 0.01  # 最大查詢時間 < 10ms
        
    @pytest.mark.benchmark
    @pytest.mark.asyncio
    async def test_memory_efficiency(self, setup):
        """記憶體效率基準測試"""
        import psutil
        import os
        
        process = psutil.Process(os.getpid())
        initial_memory = process.memory_info().rss
        
        # 執行密集操作
        model = GeminiModel(setup)
        large_responses = []
        
        with patch('google.generativeai.GenerativeModel.generate_content', new_callable=AsyncMock) as mock_generate:
            mock_generate.return_value.text = "Large response " * 1000
            
            for _ in range(100):
                response = await model.generate_text("Memory test")
                large_responses.append(response)
                
        final_memory = process.memory_info().rss
        memory_per_response = (final_memory - initial_memory) / len(large_responses)
        
        # 驗證記憶體效率
        assert memory_per_response < 1024 * 1024  # 每個響應平均使用 < 1MB 