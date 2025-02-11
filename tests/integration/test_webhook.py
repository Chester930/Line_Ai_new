import pytest
from fastapi.testclient import TestClient
from unittest.mock import Mock, patch
from src.main import create_app
from src.shared.config.manager import config_manager
from src.line.handler import line_handler
from src.shared.events.publisher import event_publisher
from src.shared.session.factory import SessionManagerFactory

@pytest.fixture
def client():
    """測試客戶端"""
    app = create_app()
    return TestClient(app)

@pytest.fixture
def line_signature():
    """LINE 簽名"""
    return "valid_signature"

@pytest.fixture
def webhook_body():
    """Webhook 請求內容"""
    return {
        "events": [{
            "type": "message",
            "message": {
                "type": "text",
                "id": "test_message_id",
                "text": "Hello, Bot!"
            },
            "source": {
                "type": "user",
                "userId": "test_user_id"
            }
        }]
    }

@pytest.mark.asyncio
async def test_webhook_flow(
    client,
    line_signature,
    webhook_body
):
    """測試完整的 webhook 流程"""
    # 模擬 LINE 簽名驗證
    with patch("linebot.WebhookHandler.handle") as mock_handle:
        # 發送 webhook 請求
        response = client.post(
            "/line/webhook",
            json=webhook_body,
            headers={"X-Line-Signature": line_signature}
        )
        
        # 驗證回應
        assert response.status_code == 200
        assert response.json() == {"status": "success"}
        
        # 驗證處理器被調用
        mock_handle.assert_called_once()

@pytest.mark.asyncio
async def test_event_handling(webhook_body):
    """測試事件處理"""
    # 創建測試事件處理器
    test_events = []
    
    class TestHandler:
        async def handle(self, event):
            test_events.append(event)
            return True
    
    # 註冊處理器
    event_publisher.subscribe(
        "message",
        TestHandler()
    )
    
    # 模擬事件處理
    with patch("linebot.WebhookHandler.handle"):
        await line_handler.handle_request(
            Mock(),
            str(webhook_body),
            "test_signature"
        )
    
    # 驗證事件
    assert len(test_events) == 1
    assert test_events[0].event_type == "message"

@pytest.mark.asyncio
async def test_session_integration():
    """測試會話整合"""
    # 創建會話管理器
    session_manager = SessionManagerFactory.create_manager()
    
    # 創建會話
    session = await session_manager.create_session(
        "test_user",
        {"source": "line"}
    )
    
    # 模擬消息處理
    with patch("linebot.LineBotApi.reply_message"):
        # 添加測試消息
        session.add_message(
            Message(
                role="user",
                content="Hello, Bot!"
            )
        )
        
        # 保存會話
        assert await session_manager.save_session(session)
        
        # 驗證消息
        loaded = await session_manager.get_session(
            session.session_id
        )
        assert loaded is not None
        assert len(loaded.messages) == 1
        assert loaded.messages[0].content == "Hello, Bot!"

@pytest.mark.asyncio
async def test_ai_integration():
    """測試 AI 整合"""
    # 創建 AI 模型
    model = AIModelFactory.create_model()
    
    # 創建測試會話
    session = Session(user_id="test_user")
    session.add_message(
        Message(
            role="user",
            content="What is Python?"
        )
    )
    
    # 模擬 AI 回應
    with patch.object(
        model.__class__,
        "generate",
        return_value=AIResponse(
            content="Python is a programming language.",
            model="test_model"
        )
    ):
        # 生成回應
        response = await model.generate(
            session.messages
        )
        
        # 驗證回應
        assert response.content == "Python is a programming language."
        assert response.model == "test_model"

def test_config_integration():
    """測試配置整合"""
    # 載入配置
    app_config = config_manager.get_app_config()
    line_config = config_manager.get_line_config()
    ai_config = config_manager.get_ai_config()
    
    # 驗證配置
    assert "debug" in app_config
    assert "channel_secret" in line_config
    assert "default_provider" in ai_config 