import pytest
from datetime import datetime
from sqlalchemy.exc import IntegrityError
from src.shared.database.models.user import User
from src.shared.database.models.conversation import Conversation

@pytest.fixture
def user_data():
    """提供測試用戶數據"""
    return {
        "line_user_id": "U123456789",
        "display_name": "Test User",
        "picture_url": "https://example.com/picture.jpg",
        "status": "active"
    }

def test_create_user(session, user_data):
    """測試創建用戶"""
    user = User(**user_data)
    session.add(user)
    session.commit()
    
    # 驗證基本屬性
    assert user.id is not None
    assert user.line_user_id == user_data["line_user_id"]
    assert user.display_name == user_data["display_name"]
    assert user.picture_url == user_data["picture_url"]
    assert user.status == user_data["status"]
    
    # 驗證時間戳
    assert isinstance(user.created_at, datetime)
    assert isinstance(user.updated_at, datetime)
    
    # 驗證默認值
    assert user.is_active is True

def test_unique_line_user_id(session, user_data):
    """測試 LINE 用戶 ID 唯一性約束"""
    # 創建第一個用戶
    user1 = User(**user_data)
    session.add(user1)
    session.commit()
    
    # 嘗試創建具有相同 LINE 用戶 ID 的用戶
    user2 = User(**user_data)
    session.add(user2)
    
    # 應該拋出 IntegrityError
    with pytest.raises(IntegrityError):
        session.commit()
    session.rollback()

def test_user_representation(session, user_data):
    """測試用戶字符串表示"""
    user = User(**user_data)
    assert str(user) == f"<User {user_data['display_name']}>"

def test_user_conversations_relationship(session, user_data):
    """測試用戶與對話的關係"""
    # 創建用戶
    user = User(**user_data)
    session.add(user)
    session.commit()
    
    # 創建對話
    conversation = Conversation(
        user_id=user.id,
        message="Hello",
        response="Hi there!",
        model="gpt-4"
    )
    session.add(conversation)
    session.commit()
    
    # 驗證關係
    assert len(user.conversations) == 1
    assert user.conversations[0].message == "Hello"
    assert user.conversations[0].user_id == user.id

def test_update_user(session, user_data):
    """測試更新用戶信息"""
    # 創建用戶
    user = User(**user_data)
    session.add(user)
    session.commit()
    
    # 記錄原始更新時間
    original_updated_at = user.updated_at
    
    # 更新用戶信息
    new_display_name = "Updated User"
    user.display_name = new_display_name
    session.commit()
    
    # 驗證更新
    assert user.display_name == new_display_name
    assert user.updated_at > original_updated_at

def test_deactivate_user(session, user_data):
    """測試停用用戶"""
    # 創建用戶
    user = User(**user_data)
    session.add(user)
    session.commit()
    
    # 停用用戶
    user.is_active = False
    user.status = "inactive"
    session.commit()
    
    # 驗證狀態
    assert user.is_active is False
    assert user.status == "inactive" 