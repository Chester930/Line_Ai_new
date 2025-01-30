import pytest
from fastapi.testclient import TestClient
from unittest.mock import Mock, patch, AsyncMock
from src.main import create_app
from src.shared.config.manager import config_manager
from src.line.handler import line_handler
from src.shared.events.publisher import event_publisher
from src.shared.session.factory import SessionManagerFactory
from src.shared.ai.factory import AIModelFactory
import json
import asyncio

@pytest.fixture
def client():
    """測試客戶端"""
    app = create_app()
    return TestClient(app)

@pytest.mark.asyncio
async def test_concurrent_webhook_handling(client):
    """測試並發 webhook 處理"""
    # 創建多個測試請求
    requests = [
        {
            "events": [{
                "type": "message",
                "message": {
                    "type": "text",
                    "id": f"msg_{i}",
                    "text": f"Message {i}"
                },
                "source": {
                    "type": "user",
                    "userId": "test_user"
                }
            }]
        } for i in range(5)
    ]
    
    async def send_request(req):
        with patch("linebot.WebhookHandler.handle"):
            response = client.post(
                "/line/webhook",
                json=req,
                headers={"X-Line-Signature": "test_signature"}
            )
            return response.status_code
    
    # 並發發送請求
    tasks = [send_request(req) for req in requests]
    results = await asyncio.gather(*tasks)
    
    # 驗證所有請求都成功
    assert all(status == 200 for status in results)

@pytest.mark.asyncio
async def test_error_handling_scenarios(client):
    """測試錯誤處理場景"""
    # 測試無效的簽名
    response = client.post(
        "/line/webhook",
        json={"events": []},
        headers={"X-Line-Signature": "invalid"}
    )
    assert response.status_code == 400
    
    # 測試無效的請求體
    response = client.post(
        "/line/webhook",
        json={"invalid": "data"},
        headers={"X-Line-Signature": "test"}
    )
    assert response.status_code == 400
    
    # 測試缺少必要字段
    response = client.post(
        "/line/webhook",
        json={"events": [{"type": "message"}]},
        headers={"X-Line-Signature": "test"}
    )
    assert response.status_code == 400

@pytest.mark.asyncio
async def test_different_message_types():
    """測試不同類型的消息處理"""
    message_types = [
        {
            "type": "text",
            "text": "Hello"
        },
        {
            "type": "image",
            "id": "test_image"
        },
        {
            "type": "location",
            "title": "My Location",
            "address": "Test Address",
            "latitude": 35.65910807942215,
            "longitude": 139.70372892916203
        }
    ]
    
    for msg_type in message_types:
        event = {
            "type": "message",
            "message": msg_type,
            "source": {
                "type": "user",
                "userId": "test_user"
            }
        }
        
        with patch("linebot.WebhookHandler.handle"):
            result = await line_handler.handle_request(
                Mock(),
                json.dumps({"events": [event]}),
                "test_signature"
            )
            assert result is True

@pytest.mark.asyncio
async def test_ai_response_integration():
    """測試 AI 響應整合"""
    # 模擬 AI 模型
    mock_model = AsyncMock()
    mock_model.generate.return_value = {
        "content": "Test response",
        "model": "test_model"
    }
    
    with patch("src.shared.ai.factory.AIModelFactory.create_model", return_value=mock_model):
        # 創建測試事件
        event = {
            "type": "message",
            "message": {
                "type": "text",
                "text": "Test message"
            },
            "source": {
                "type": "user",
                "userId": "test_user"
            }
        }
        
        # 處理請求
        with patch("linebot.WebhookHandler.handle"):
            result = await line_handler.handle_request(
                Mock(),
                json.dumps({"events": [event]}),
                "test_signature"
            )
        
        # 驗證 AI 模型被調用
        mock_model.generate.assert_called_once()
        assert result is True

@pytest.mark.asyncio
async def test_session_state_management():
    """測試會話狀態管理"""
    session_manager = SessionManagerFactory.create_manager()
    
    # 創建初始會話
    session = await session_manager.create_session("test_user")
    
    # 模擬多輪對話
    conversations = [
        ("User message 1", "Bot response 1"),
        ("User message 2", "Bot response 2"),
        ("User message 3", "Bot response 3")
    ]
    
    for user_msg, bot_msg in conversations:
        # 添加用戶消息
        session.add_message({
            "role": "user",
            "content": user_msg
        })
        
        # 添加機器人響應
        session.add_message({
            "role": "assistant",
            "content": bot_msg
        })
        
        # 保存會話
        await session_manager.save_session(session)
        
        # 重新加載會話
        loaded_session = await session_manager.get_session(session.id)
        assert loaded_session is not None
        
        # 驗證消息歷史
        messages = loaded_session.get_messages()
        assert len(messages) == len(session.get_messages())
        assert messages[-2]["content"] == user_msg
        assert messages[-1]["content"] == bot_msg 