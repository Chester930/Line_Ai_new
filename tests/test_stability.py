import pytest
import asyncio
import time
import random
from unittest.mock import AsyncMock, patch
from src.shared.ai.models.gemini import GeminiModel
from src.shared.line_sdk.client import LineClient
from src.shared.database.base import Database
from src.shared.config.base import ConfigManager
from src.shared.events.base import EventEmitter
from src.shared.utils.logger import logger

class TestStability:
    @pytest.fixture
    def config(self):
        config = ConfigManager()
        config.set("GOOGLE_API_KEY", "test_api_key")
        config.set("LINE_CHANNEL_SECRET", "test_secret")
        config.set("LINE_CHANNEL_ACCESS_TOKEN", "test_token")
        return config
        
    @pytest.mark.asyncio
    async def test_long_running_stability(self, config):
        """測試長時間運行穩定性"""
        model = GeminiModel(config)
        client = LineClient(
            channel_secret=config.get("LINE_CHANNEL_SECRET"),
            channel_access_token=config.get("LINE_CHANNEL_ACCESS_TOKEN")
        )
        
        start_time = time.time()
        test_duration = 300  # 5分鐘測試
        request_count = 0
        error_count = 0
        
        while time.time() - start_time < test_duration:
            try:
                with patch('google.generativeai.GenerativeModel.generate_content', new_callable=AsyncMock) as mock_generate:
                    mock_generate.return_value.text = "Test response"
                    response = await model.generate_text("Test message")
                    
                    with patch('linebot.AsyncLineBotApi.push_message', new_callable=AsyncMock):
                        await client.send_text("test_user", response)
                        
                request_count += 1
                await asyncio.sleep(0.1)  # 控制請求頻率
            except Exception as e:
                error_count += 1
                logger.error(f"Error during stability test: {str(e)}")
                
        error_rate = error_count / request_count if request_count > 0 else 1
        assert error_rate < 0.01  # 長期錯誤率應小於1%
        assert request_count > 0  # 確保有處理請求
        
    @pytest.mark.asyncio
    async def test_memory_leak(self, config):
        """測試記憶體洩漏"""
        import psutil
        process = psutil.Process()
        
        initial_memory = process.memory_info().rss
        model = GeminiModel(config)
        
        # 執行大量操作
        for _ in range(1000):
            with patch('google.generativeai.GenerativeModel.generate_content', new_callable=AsyncMock) as mock_generate:
                mock_generate.return_value.text = "Test response"
                await model.generate_text("Test message")
                await asyncio.sleep(0.01)
                
        # 強制垃圾回收
        import gc
        gc.collect()
        
        final_memory = process.memory_info().rss
        memory_growth = final_memory - initial_memory
        
        # 記憶體增長不應超過 10MB
        assert memory_growth < 10 * 1024 * 1024
        
    @pytest.mark.asyncio
    async def test_connection_stability(self, config):
        """測試連接穩定性"""
        db = Database("sqlite+aiosqlite:///:memory:")
        
        async def db_operation():
            try:
                async with db.session() as session:
                    await session.execute("SELECT 1")
                    await session.commit()
                return True
            except Exception:
                return False
                
        success_count = 0
        total_attempts = 100
        
        # 模擬網絡不穩定
        for _ in range(total_attempts):
            if random.random() < 0.2:  # 20% 機率模擬網絡延遲
                await asyncio.sleep(random.uniform(0.1, 0.5))
            
            if await db_operation():
                success_count += 1
                
        success_rate = success_count / total_attempts
        assert success_rate > 0.95  # 連接成功率應大於95%
        
    @pytest.mark.asyncio
    async def test_recovery_mechanism(self, config):
        """測試系統恢復機制"""
        model = GeminiModel(config)
        event_emitter = EventEmitter()
        recovery_count = 0
        
        async def error_handler(error: Exception, event: dict):
            nonlocal recovery_count
            recovery_count += 1
            logger.info(f"Recovered from error: {str(error)}")
            
        event_emitter.on_error(error_handler)
        
        # 模擬系統故障和恢復
        for _ in range(50):
            try:
                with patch('google.generativeai.GenerativeModel.generate_content', new_callable=AsyncMock) as mock_generate:
                    if random.random() < 0.3:  # 30% 故障率
                        mock_generate.side_effect = Exception("Simulated failure")
                    else:
                        mock_generate.return_value.text = "Test response"
                    await model.generate_text("Test message")
            except Exception as e:
                await event_emitter.emit({
                    "type": "error",
                    "data": {"error": str(e)}
                })
                
        assert recovery_count > 0  # 確保恢復機制被觸發
        assert recovery_count < 25  # 故障恢復次數應在合理範圍 