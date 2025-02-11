import pytest
from src.shared.chat.handlers.manager import MessageHandlerManager
from src.shared.chat.session import Message
from src.shared.chat.handlers.base import BaseMessageHandler

@pytest.fixture
def handler_manager():
    return MessageHandlerManager()

@pytest.fixture
def test_message():
    return Message(
        content="test",
        role="user",
        type="text"
    )

def test_manager_initialization(handler_manager):
    """測試管理器初始化"""
    assert "text" in handler_manager._handlers
    assert "image" in handler_manager._handlers

def test_handler_registration(handler_manager):
    """測試處理器註冊"""
    class CustomHandler(BaseMessageHandler):
        async def handle(self, message):
            return {"success": True}
        async def validate(self, message):
            return True
    
    handler_manager.register_handler("custom", CustomHandler())
    assert "custom" in handler_manager._handlers

@pytest.mark.asyncio
async def test_message_handling(handler_manager, test_message):
    """測試消息處理"""
    result = await handler_manager.handle_message(test_message)
    assert "success" in result

@pytest.mark.asyncio
async def test_invalid_message_type(handler_manager):
    """測試無效消息類型"""
    invalid_message = Message(
        content="test",
        role="user",
        type="invalid"
    )
    result = await handler_manager.handle_message(invalid_message)
    assert not result["success"]
    assert "error" in result 