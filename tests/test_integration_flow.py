import pytest
import asyncio
from unittest.mock import AsyncMock, patch
from src.shared.ai.models.gemini import GeminiModel
from src.shared.line_sdk.client import LineClient
from src.shared.database.base import Database
from src.shared.events.base import EventEmitter
from src.shared.config.base import ConfigManager

class TestIntegrationFlow:
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
        emitter = EventEmitter()
        
        return {
            "config": config,
            "model": model,
            "client": client,
            "db": db,
            "emitter": emitter
        }
        
    @pytest.mark.asyncio
    async def test_complete_conversation_flow(self, setup):
        """測試完整對話流程"""
        model = setup["model"]
        client = setup["client"]
        db = setup["db"]
        
        # 1. 用戶發送消息
        user_message = "Hello, AI!"
        
        # 2. 生成 AI 回應
        with patch('google.generativeai.GenerativeModel.generate_content', new_callable=AsyncMock) as mock_generate:
            mock_generate.return_value.text = "Hi! How can I help you?"
            ai_response = await model.generate_text(user_message)
            
            # 3. 發送回應
            with patch('linebot.AsyncLineBotApi.reply_message', new_callable=AsyncMock) as mock_reply:
                await client.send_text("test_user", ai_response)
                
                # 4. 驗證數據庫記錄
                async with db.session() as session:
                    result = await session.execute(
                        "SELECT * FROM conversations ORDER BY created_at DESC LIMIT 2"
                    )
                    conversations = result.fetchall()
                    assert len(conversations) == 2
                    
    @pytest.mark.asyncio
    async def test_concurrent_users(self, setup):
        """測試多用戶並發"""
        model = setup["model"]
        client = setup["client"]
        
        async def user_conversation(user_id: str):
            with patch('google.generativeai.GenerativeModel.generate_content', new_callable=AsyncMock) as mock_generate:
                mock_generate.return_value.text = f"Response to user {user_id}"
                response = await model.generate_text(f"Message from {user_id}")
                
                with patch('linebot.AsyncLineBotApi.push_message', new_callable=AsyncMock) as mock_push:
                    await client.send_text(user_id, response)
                    return response
                    
        # 模擬10個用戶同時對話
        users = [f"user_{i}" for i in range(10)]
        tasks = [user_conversation(user_id) for user_id in users]
        
        responses = await asyncio.gather(*tasks)
        assert len(responses) == 10
        
    @pytest.mark.asyncio
    async def test_system_recovery(self, setup):
        """測試系統恢復流程"""
        model = setup["model"]
        emitter = setup["emitter"]
        db = setup["db"]
        
        # 模擬系統故障
        with patch('google.generativeai.GenerativeModel.generate_content', new_callable=AsyncMock) as mock_generate:
            mock_generate.side_effect = Exception("API Error")
            
            try:
                await model.generate_text("Test message")
            except Exception:
                # 觸發恢復流程
                await emitter.emit({
                    "type": "error",
                    "data": {"error": "API Error"}
                })
                
                # 驗證錯誤記錄
                async with db.session() as session:
                    result = await session.execute(
                        "SELECT * FROM error_logs ORDER BY created_at DESC LIMIT 1"
                    )
                    error_log = result.fetchone()
                    assert error_log is not None
                    assert "API Error" in error_log.message
                    
    @pytest.mark.asyncio
    async def test_data_consistency(self, setup):
        """測試數據一致性"""
        db = setup["db"]
        
        async def concurrent_operations():
            async with db.session() as session:
                # 創建用戶
                await session.execute(
                    "INSERT INTO users (name) VALUES (:name)",
                    {"name": "test_user"}
                )
                await session.commit()
                
                # 讀取用戶
                result = await session.execute(
                    "SELECT * FROM users WHERE name = :name",
                    {"name": "test_user"}
                )
                user = result.fetchone()
                assert user is not None
                
                # 更新用戶
                await session.execute(
                    "UPDATE users SET name = :new_name WHERE name = :old_name",
                    {"new_name": "updated_user", "old_name": "test_user"}
                )
                await session.commit()
                
        # 執行並發操作
        tasks = [concurrent_operations() for _ in range(5)]
        await asyncio.gather(*tasks)
        
        # 驗證最終狀態
        async with db.session() as session:
            result = await session.execute("SELECT COUNT(*) FROM users")
            count = result.scalar()
            assert count == 5 