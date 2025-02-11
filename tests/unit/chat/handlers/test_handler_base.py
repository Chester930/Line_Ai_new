import pytest
from src.shared.chat.handlers.base import BaseMessageHandler
from src.shared.chat.session import Message
from src.shared.utils.types import Callable
from typing import Dict, Any

class TestHandler(BaseMessageHandler):
    """測試用處理器"""
    async def handle(self, message: Message) -> Dict[str, Any]:
        return {"success": True}
    
    async def validate(self, message: Message) -> bool:
        return True

@pytest.fixture
def handler():
    return TestHandler()

@pytest.fixture
def test_message():
    return Message(
        content="test",
        role="user",
        type="text"
    )

@pytest.mark.asyncio
async def test_base_handler_preprocess(handler, test_message):
    """測試預處理"""
    processed = await handler.preprocess(test_message)
    assert processed == test_message

@pytest.mark.asyncio
async def test_base_handler_postprocess(handler):
    """測試後處理"""
    result = {"success": True}
    processed = await handler.postprocess(result)
    assert processed == result

@pytest.mark.asyncio
async def test_base_handler_error(handler):
    """測試錯誤處理"""
    error = Exception("test error")
    result = await handler.handle_error(error)
    assert result["success"] == False
    assert "error" in result 