import pytest
from unittest.mock import AsyncMock, patch
from src.shared.ai.models.gemini import GeminiModel
from src.shared.ai.prompts.roles import AssistantPrompt
from src.shared.line_sdk.client import LineClient
from src.shared.line_sdk.webhook import WebhookHandler
from src.shared.events.types import Event
from src.shared.config.base import ConfigManager
from src.shared.database.models.user import User
from src.shared.database.models.conversation import Conversation

class TestIntegration:
    @pytest.fixture
    def config(self):
        """配置測試夾具"""
        config = ConfigManager()
        config.set("GOOGLE_API_KEY", "test_api_key")
        config.set("LINE_CHANNEL_SECRET", "test_secret")
        config.set("LINE_CHANNEL_ACCESS_TOKEN", "test_token")
        return config
        
    @pytest.fixture
    def ai_model(self, config):
        """AI 模型測試夾具"""
        return GeminiModel(config)
        
    @pytest.fixture
    def line_client(self, config):
        """LINE 客戶端測試夾具"""
        return LineClient(
            channel_secret=config.get("LINE_CHANNEL_SECRET"),
            channel_access_token=config.get("LINE_CHANNEL_ACCESS_TOKEN")
        )
        
    @pytest.fixture
    def prompt(self, config):
        """提示詞測試夾具"""
        return AssistantPrompt(config)
        
    @pytest.mark.asyncio
    async def test_complete_conversation_flow(self, ai_model, line_client, prompt, config):
        """測試完整對話流程"""
        # 模擬用戶發送消息
        user_message = "What is Python?"
        
        # 1. 生成提示詞
        prompt_text = prompt.build(user_message)
        assert "Python" in prompt_text
        
        # 2. 生成 AI 回應
        with patch('google.generativeai.GenerativeModel.generate_content', new_callable=AsyncMock) as mock_generate:
            mock_generate.return_value.text = "Python is a programming language."
            ai_response = await ai_model.generate_text(prompt_text)
            assert "programming language" in ai_response
            
        # 3. 發送回應給用戶
        with patch('linebot.AsyncLineBotApi.reply_message', new_callable=AsyncMock) as mock_reply:
            await line_client.send_text(
                user_id="test_user",
                text=ai_response
            )
            mock_reply.assert_called_once()
            
    @pytest.mark.asyncio
    async def test_conversation_persistence(self, ai_model, line_client, prompt, config):
        """測試對話持久化"""
        async with Database("sqlite+aiosqlite:///:memory:").session() as session:
            # 1. 創建用戶記錄
            user = User(line_id="test_user")
            session.add(user)
            await session.commit()
            
            # 2. 記錄用戶消息
            user_conv = Conversation(
                user_id=user.id,
                message="What is Python?",
                role="user"
            )
            session.add(user_conv)
            await session.commit()
            
            # 3. 生成並記錄 AI 回應
            with patch('google.generativeai.GenerativeModel.generate_content', new_callable=AsyncMock) as mock_generate:
                mock_generate.return_value.text = "Python is a programming language."
                ai_response = await ai_model.generate_text(user_conv.message)
                
                ai_conv = Conversation(
                    user_id=user.id,
                    message=ai_response,
                    role="assistant"
                )
                session.add(ai_conv)
                await session.commit()
                
            # 4. 驗證對話歷史
            conversations = await session.execute(
                select(Conversation).where(Conversation.user_id == user.id)
            )
            conversations = conversations.scalars().all()
            assert len(conversations) == 2
            assert conversations[0].role == "user"
            assert conversations[1].role == "assistant"
            
    @pytest.mark.asyncio
    async def test_error_handling_flow(self, ai_model, line_client, prompt, config):
        """測試錯誤處理流程"""
        # 1. 模擬 AI 模型錯誤
        with patch('google.generativeai.GenerativeModel.generate_content', new_callable=AsyncMock) as mock_generate:
            mock_generate.side_effect = Exception("API Error")
            
            # 2. 確保錯誤被捕獲並發送適當的錯誤消息
            with patch('linebot.AsyncLineBotApi.push_message', new_callable=AsyncMock) as mock_push:
                try:
                    await ai_model.generate_text("Test message")
                except Exception:
                    await line_client.send_text(
                        user_id="test_user",
                        text="Sorry, I encountered an error. Please try again later."
                    )
                    
                mock_push.assert_called_once()
                
    @pytest.mark.asyncio
    async def test_context_preservation(self, ai_model, prompt, config):
        """測試上下文保持"""
        # 1. 設置對話上下文
        context = [
            {"role": "user", "content": "What is Python?"},
            {"role": "assistant", "content": "Python is a programming language."},
            {"role": "user", "content": "Tell me more about it."}
        ]
        
        # 2. 使用上下文生成回應
        with patch('google.generativeai.GenerativeModel.generate_content', new_callable=AsyncMock) as mock_generate:
            mock_generate.return_value.text = "Python is known for its simplicity."
            
            ai_model.set_context(context)
            response = await ai_model.generate_text("Continue")
            
            # 3. 驗證上下文被正確使用
            call_args = mock_generate.call_args[0]
            assert len(call_args[0]) > 1
            assert "simplicity" in response 