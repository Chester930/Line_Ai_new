import pytest
from uuid import uuid4
from datetime import datetime
from src.shared.session.base import Message, Session  # 修正導入路徑

@pytest.fixture
def test_session():
    return Session("test_session", "test_user")

@pytest.mark.asyncio
async def test_session_message_operations(test_session):
    """測試會話消息操作"""
    # 添加消息
    message = Message(
        id=uuid4(),
        role="user",
        content="test",
        user_id="test_user",
        type="text",
        timestamp=datetime.now()  # 添加必要的時間戳
    )
    await test_session.add_message(message)
    
    # 獲取消息
    messages = test_session.get_messages()
    assert len(messages) == 1
    assert messages[0].content == "test"
    
    # 清空消息
    test_session.clear_messages()
    assert len(test_session.messages) == 0

@pytest.mark.asyncio
async def test_session_metadata_operations(test_session):
    """測試會話元數據操作"""
    # 更新元數據
    test_session.update_metadata({"key": "value"})
    assert test_session.data["key"] == "value"
    
    # 移除元數據
    test_session.remove_metadata("key")
    assert "key" not in test_session.data

def test_session_serialization(test_session):
    """測試會話序列化"""
    # 添加一些數據
    test_session.data["test"] = "value"
    
    # 轉換為字典
    data = test_session.to_dict()
    assert data["id"] == test_session.id
    assert data["user_id"] == test_session.user_id
    assert data["data"]["test"] == "value"
    
    # 從字典創建
    new_session = Session.from_dict(data)
    assert new_session.id == test_session.id
    assert new_session.data["test"] == "value" 