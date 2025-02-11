import pytest
from datetime import datetime
from sqlalchemy.exc import IntegrityError
from src.shared.database.models.user import User
from src.shared.database.models.conversation import Conversation

@pytest.fixture
def user(session):
    """提供測試用戶"""
    user = User(
        line_user_id="U123456789",
        display_name="Test User"
    )
    session.add(user)
    session.commit()
    return user

@pytest.fixture
def conversation_data(user):
    """提供測試對話數據"""
    return {
        "user_id": user.id,
        "message": "Hello, AI!",
        "response": "Hi there! How can I help you?",
        "model": "gpt-4",
        "status": "completed"
    }

def test_create_conversation(session, conversation_data):
    """測試創建對話"""
    conversation = Conversation(**conversation_data)
    session.add(conversation)
    session.commit()
    
    # 驗證基本屬性
    assert conversation.id is not None
    assert conversation.user_id == conversation_data["user_id"]
    assert conversation.message == conversation_data["message"]
    assert conversation.response == conversation_data["response"]
    assert conversation.model == conversation_data["model"]
    assert conversation.status == conversation_data["status"]
    
    # 驗證時間戳
    assert isinstance(conversation.created_at, datetime)

def test_conversation_user_relationship(session, user, conversation_data):
    """測試對話與用戶的關係"""
    conversation = Conversation(**conversation_data)
    session.add(conversation)
    session.commit()
    
    # 驗證關係
    assert conversation.user == user
    assert conversation in user.conversations

def test_conversation_representation(session, conversation_data):
    """測試對話字符串表示"""
    conversation = Conversation(**conversation_data)
    session.add(conversation)
    session.commit()
    
    assert str(conversation) == f"<Conversation {conversation.id}>"

def test_conversation_cascade_delete(session, user, conversation_data):
    """測試級聯刪除"""
    # 創建對話
    conversation = Conversation(**conversation_data)
    session.add(conversation)
    session.commit()
    
    # 刪除用戶
    session.delete(user)
    session.commit()
    
    # 驗證對話也被刪除
    assert session.query(Conversation).count() == 0

def test_conversation_status_update(session, conversation_data):
    """測試更新對話狀態"""
    conversation = Conversation(**conversation_data)
    session.add(conversation)
    session.commit()
    
    # 更新狀態
    new_status = "archived"
    conversation.status = new_status
    session.commit()
    
    # 驗證更新
    assert conversation.status == new_status

def test_conversation_without_user(session):
    """測試創建沒有用戶的對話（應該失敗）"""
    conversation = Conversation(
        message="Test message",
        response="Test response",
        model="gpt-4"
    )
    session.add(conversation)
    
    # 應該拋出 IntegrityError
    with pytest.raises(IntegrityError):
        session.commit()
    session.rollback()

def test_multiple_conversations_per_user(session, user):
    """測試一個用戶的多個對話"""
    # 創建多個對話
    conversations = []
    for i in range(3):
        conversation = Conversation(
            user_id=user.id,
            message=f"Message {i}",
            response=f"Response {i}",
            model="gpt-4",
            status="completed"
        )
        session.add(conversation)
        conversations.append(conversation)
    session.commit()
    
    # 驗證用戶的對話數量
    assert len(user.conversations) == 3
    
    # 驗證對話順序（按創建時間）
    for i, conversation in enumerate(user.conversations):
        assert conversation.message == f"Message {i}" 