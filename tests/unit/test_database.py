import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from src.shared.database.base import Base
from src.shared.database.models.user import User
from src.shared.database.models.conversation import Conversation

@pytest.fixture
def session():
    # 使用 SQLite 內存數據庫進行測試
    engine = create_engine('sqlite:///:memory:', echo=True)
    SessionLocal = sessionmaker(bind=engine)
    
    # 創建所有表
    Base.metadata.create_all(bind=engine)
    
    # 提供會話
    session = SessionLocal()
    try:
        yield session
    finally:
        session.close()
        Base.metadata.drop_all(bind=engine)

def test_create_user(session: Session):
    user = User(
        line_user_id="U123456789",
        display_name="Test User"
    )
    session.add(user)
    session.commit()
    
    assert user.id is not None
    assert user.line_user_id == "U123456789"

def test_create_conversation(session: Session):
    # 創建用戶
    user = User(line_user_id="U123456789", display_name="Test User")
    session.add(user)
    session.commit()

    # 創建對話
    conv = Conversation(
        user_id=user.id,
        message="Hello",
        response="Hi there!",
        model="gpt-4"
    )
    session.add(conv)
    session.commit()

    assert conv.id is not None
    assert conv.user_id == user.id 