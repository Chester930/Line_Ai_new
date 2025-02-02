import pytest
from datetime import datetime, timedelta
from src.shared.session.base import Session, Message, AIResponse
from uuid import uuid4

@pytest.fixture
def test_session():
    return Session("test_session", "test_user")

class TestSession:
    def test_init(self, test_session):
        assert test_session.id == "test_session"
        assert test_session.user_id == "test_user"
        assert isinstance(test_session.created_at, datetime)
        assert isinstance(test_session.last_activity, datetime)
        
    async def test_add_message(self, test_session):
        message = Message(
            id=uuid4(),
            role="user",
            content="test message",
            user_id="test_user"
        )
        success = await test_session.add_message(message)
        assert success
        assert len(test_session.messages) == 1
        
    @pytest.mark.asyncio
    async def test_get_messages(self, test_session):
        # 添加測試消息
        messages = [
            Message(
                id=uuid4(),
                role="user",
                content=f"message {i}",
                user_id="test_user",
                type="text"
            )
            for i in range(3)
        ]
        for msg in messages:
            await test_session.add_message(msg)
            
        # 測試不同的過濾條件
        all_messages = test_session.get_messages()
        assert len(all_messages) == 3
        
        text_messages = test_session.get_messages(message_type="text")
        assert len(text_messages) == 3
        
        limited_messages = test_session.get_messages(limit=2)
        assert len(limited_messages) == 2
        
    @pytest.mark.asyncio
    async def test_get_messages_with_time_range(self, test_session):
        # 創建固定的基準時間，避免時間差異
        base_time = datetime(2024, 1, 1, 12, 0, 0)  # 使用固定時間
        
        # 創建三條消息，間隔1分鐘
        messages = []
        for i in range(3):
            message = Message(
                id=uuid4(),
                role="user",
                content=f"message {i}",
                user_id="test_user",
                type="text",
                timestamp=base_time - timedelta(minutes=i)
            )
            messages.append(message)
            await test_session.add_message(message)
        
        # 驗證消息順序 (從舊到新)
        assert [msg.content for msg in test_session.get_messages()] == [
            "message 2",  # 最舊的消息 (2分鐘前)
            "message 1",  # 1分鐘前的消息
            "message 0"   # 最新的消息
        ]
        
        # 測試時間範圍過濾
        # 只獲取最近1.5分鐘內的消息 (從舊到新)
        start_time = base_time - timedelta(minutes=1, seconds=30)
        filtered_messages = test_session.get_messages(start_time=start_time)
        assert [msg.content for msg in filtered_messages] == [
            "message 1",  # 1分鐘前的消息
            "message 0"   # 最新的消息
        ]
        
        # 測試結束時間過濾
        # 只獲取1分鐘前的消息 (從舊到新)
        end_time = base_time - timedelta(minutes=1)
        filtered_messages = test_session.get_messages(end_time=end_time)
        assert [msg.content for msg in filtered_messages] == [
            "message 2",  # 2分鐘前的消息
            "message 1"   # 1分鐘前的消息
        ]
        
        # 測試時間範圍組合：獲取1-2分鐘之間的消息
        filtered_messages = test_session.get_messages(
            start_time=base_time - timedelta(minutes=2),  # 2分鐘前
            end_time=base_time - timedelta(minutes=1)     # 1分鐘前
        )
        assert [msg.content for msg in filtered_messages] == ["message 2", "message 1"], \
            f"Expected ['message 2', 'message 1'], got {[msg.content for msg in filtered_messages]}"
        
    @pytest.mark.asyncio
    async def test_get_messages_edge_cases(self, test_session):
        base_time = datetime.now()
        
        # 創建測試消息
        message = Message(
            id=uuid4(),
            role="user",
            content="test message",
            user_id="test_user",
            type="text",
            timestamp=base_time
        )
        await test_session.add_message(message)
        
        # 測試邊界情況
        # 1. 開始時間等於消息時間
        filtered = test_session.get_messages(start_time=base_time)
        assert len(filtered) == 1
        
        # 2. 結束時間等於消息時間
        filtered = test_session.get_messages(end_time=base_time)
        assert len(filtered) == 1
        
        # 3. 時間範圍不包含任何消息
        filtered = test_session.get_messages(
            start_time=base_time + timedelta(seconds=1)
        )
        assert len(filtered) == 0
        
    def test_update_metadata(self, test_session):
        test_session.update_metadata({"key": "value"})
        assert test_session.data["key"] == "value"
        
        test_session.remove_metadata("key")
        assert "key" not in test_session.data
        
    def test_to_dict(self, test_session):
        data = test_session.to_dict()
        assert data["id"] == test_session.id
        assert data["user_id"] == test_session.user_id
        assert "created_at" in data
        assert "last_activity" in data
        
    def test_from_dict(self):
        data = {
            "id": "test_session",
            "user_id": "test_user",
            "created_at": datetime.now().isoformat(),
            "last_activity": datetime.now().isoformat(),
            "ttl": 3600,
            "data": {},
            "messages": []
        }
        session = Session.from_dict(data)
        assert session.id == data["id"]
        assert session.user_id == data["user_id"]
        
    def test_is_expired(self, test_session):
        # 未過期的情況
        assert not test_session.is_expired()
        
        # 設置為過期
        test_session.last_activity = datetime.now() - timedelta(seconds=test_session.ttl + 1)
        assert test_session.is_expired()
        
        # 更新活動時間
        test_session.update_activity()
        assert not test_session.is_expired()

    def test_message_serialization(self):
        message = Message(
            id=uuid4(),
            role="user",
            content="test message",
            user_id="test_user",
            type="text",
            metadata={"key": "value"}
        )
        
        # 轉換為字典
        data = {
            "id": str(message.id),
            "role": message.role,
            "content": message.content,
            "user_id": message.user_id,
            "type": message.type,
            "timestamp": message.timestamp.isoformat(),
            "metadata": message.metadata
        }
        
        # 從字典創建
        new_message = Message(**data)
        assert str(new_message.id) == data["id"]
        assert new_message.role == data["role"]
        assert new_message.content == data["content"]
        assert new_message.metadata == data["metadata"]

@pytest.mark.asyncio
async def test_session_message_operations(test_session):
    """測試會話消息操作"""
    message = Message(
        id=uuid4(),
        role="user",
        content="test",
        user_id="test_user",
        type="text",
        timestamp=datetime.now()
    )
    await test_session.add_message(message)
    
    # 測試消息過濾
    messages = test_session.get_messages(message_type="text")
    assert len(messages) == 1
    
    # 測試時間範圍過濾
    messages = test_session.get_messages(
        start_time=datetime.now() - timedelta(minutes=5)
    )
    assert len(messages) == 1 