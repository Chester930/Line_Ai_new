import pytest
import asyncio
import time
import psutil
import os
from unittest.mock import AsyncMock, patch
from src.shared.ai.models.gemini import GeminiModel
from src.shared.line_sdk.client import LineClient
from src.shared.database.base import Database
from src.shared.config.base import ConfigManager
from src.shared.utils.logger import logger

class TestMonitoring:
    @pytest.fixture
    def config(self):
        config = ConfigManager()
        config.set("GOOGLE_API_KEY", "test_api_key")
        config.set("LINE_CHANNEL_SECRET", "test_secret")
        config.set("LINE_CHANNEL_ACCESS_TOKEN", "test_token")
        return config
        
    @pytest.mark.asyncio
    async def test_system_metrics(self, config):
        """測試系統指標監控"""
        process = psutil.Process(os.getpid())
        
        # 基準指標
        initial_metrics = {
            'cpu_percent': process.cpu_percent(),
            'memory_percent': process.memory_percent(),
            'threads': len(process.threads()),
            'connections': len(process.connections())
        }
        
        # 執行負載操作
        model = GeminiModel(config)
        tasks = []
        for _ in range(50):
            with patch('google.generativeai.GenerativeModel.generate_content', new_callable=AsyncMock) as mock_generate:
                mock_generate.return_value.text = "Test response"
                tasks.append(model.generate_text("Test message"))
                
        await asyncio.gather(*tasks)
        
        # 檢查資源使用
        final_metrics = {
            'cpu_percent': process.cpu_percent(),
            'memory_percent': process.memory_percent(),
            'threads': len(process.threads()),
            'connections': len(process.connections())
        }
        
        # 驗證資源使用在合理範圍
        assert final_metrics['cpu_percent'] < 80  # CPU 使用率應小於 80%
        assert final_metrics['memory_percent'] < 70  # 記憶體使用率應小於 70%
        assert final_metrics['threads'] - initial_metrics['threads'] < 10  # 線程增加不超過 10 個
        
    @pytest.mark.asyncio
    async def test_response_time_distribution(self, config):
        """測試響應時間分佈"""
        model = GeminiModel(config)
        response_times = []
        
        async def measure_response_time():
            start = time.time()
            with patch('google.generativeai.GenerativeModel.generate_content', new_callable=AsyncMock) as mock_generate:
                mock_generate.return_value.text = "Test response"
                await model.generate_text("Test message")
            response_times.append(time.time() - start)
            
        # 執行100次請求
        tasks = [measure_response_time() for _ in range(100)]
        await asyncio.gather(*tasks)
        
        # 計算統計指標
        avg_time = sum(response_times) / len(response_times)
        p95_time = sorted(response_times)[int(len(response_times) * 0.95)]
        p99_time = sorted(response_times)[int(len(response_times) * 0.99)]
        
        # 驗證性能指標
        assert avg_time < 0.5  # 平均響應時間 < 500ms
        assert p95_time < 1.0  # 95% 請求 < 1s
        assert p99_time < 2.0  # 99% 請求 < 2s
        
    @pytest.mark.asyncio
    async def test_error_monitoring(self, config):
        """測試錯誤監控"""
        model = GeminiModel(config)
        error_count = 0
        total_requests = 100
        
        async def error_test():
            nonlocal error_count
            try:
                with patch('google.generativeai.GenerativeModel.generate_content', new_callable=AsyncMock) as mock_generate:
                    # 隨機模擬錯誤
                    if time.time() % 3 == 0:
                        mock_generate.side_effect = Exception("API Error")
                    else:
                        mock_generate.return_value.text = "Test response"
                    await model.generate_text("Test message")
            except Exception as e:
                error_count += 1
                logger.error(f"Error in request: {str(e)}")
                
        tasks = [error_test() for _ in range(total_requests)]
        await asyncio.gather(*tasks)
        
        error_rate = error_count / total_requests
        assert error_rate < 0.1  # 錯誤率應小於 10%
        
    @pytest.mark.asyncio
    async def test_database_metrics(self, config):
        """測試數據庫指標"""
        db = Database("sqlite+aiosqlite:///:memory:")
        query_times = []
        
        async def measure_query_time():
            async with db.session() as session:
                start = time.time()
                await session.execute("SELECT 1")
                query_times.append(time.time() - start)
                
        # 執行100次查詢
        tasks = [measure_query_time() for _ in range(100)]
        await asyncio.gather(*tasks)
        
        # 計算統計指標
        avg_query_time = sum(query_times) / len(query_times)
        max_query_time = max(query_times)
        
        assert avg_query_time < 0.01  # 平均查詢時間 < 10ms
        assert max_query_time < 0.1  # 最大查詢時間 < 100ms 