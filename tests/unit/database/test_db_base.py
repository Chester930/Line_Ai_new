import pytest
from sqlalchemy.orm import Session
from sqlalchemy import inspect, text
from sqlalchemy.exc import SQLAlchemyError
from src.shared.database.base import Database
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import Column, String
from src.shared.utils.types import Optional

@pytest.fixture
def db():
    """數據庫測試夾具"""
    database = Database()
    database.create_tables()  # 確保表已創建
    return database

@pytest.fixture
def db_session(db):
    """提供測試數據庫會話"""
    session = next(db.get_session())
    try:
        yield session
        session.commit()  # 提交更改
    finally:
        session.close()

def test_database_connection(db):
    """測試數據庫連接"""
    assert db._engine is not None
    assert db._session_factory is not None  # 使用正確的屬性名稱

def test_session_management(db):
    """測試會話管理"""
    session = next(db.get_session())
    assert session is not None
    session.close()

def test_database_initialization(db):
    """測試數據庫初始化"""
    # 測試單例模式
    db2 = Database()
    assert db is db2
    
    # 測試初始化狀態
    assert db._initialized is True
    assert isinstance(db, Database)
    
    # 測試創建表
    try:
        db.create_tables()
        assert True  # 如果沒有拋出異常，則測試通過
    except Exception as e:
        pytest.fail(f"創建表失敗: {str(e)}")

def test_session_rollback(db):
    """測試會話回滾"""
    session = next(db.get_session())
    try:
        # 模擬錯誤操作
        raise SQLAlchemyError("Test error")
    except SQLAlchemyError:
        session.rollback()
    finally:
        session.close()

def test_base_class():
    """測試 Base 類"""
    assert isinstance(Base.metadata, type(Base.metadata))

def test_session_rollback(db_session):
    """測試會話回滾"""
    try:
        # 使用 text() 來執行原始 SQL
        db_session.execute(text("SELECT * FROM non_existent_table"))
        db_session.commit()
        assert False, "應該拋出異常"
    except Exception:
        db_session.rollback()
        assert db_session.is_active 

@pytest.mark.asyncio
async def test_database_operations(db_session):
    """測試數據庫操作"""
    # 創建測試模型
    class TestModel(Base):
        __tablename__ = 'test_model'
        __table_args__ = {'extend_existing': True}
        
        id = Column(String, primary_key=True)
        data = Column(String)
        
        def __init__(self, id, data):
            self.id = id
            self.data = data
    
    # 清理現有表
    TestModel.__table__.drop(bind=db_session.bind, checkfirst=True)
    
    # 創建表
    TestModel.__table__.create(bind=db_session.bind, checkfirst=True)
    
    try:
        # 使用同步方式操作
        model = TestModel("test_id", "test_data")
        db_session.add(model)
        db_session.commit()
        
        # 測試查詢
        result = db_session.query(TestModel).filter_by(id="test_id").first()
        assert result.id == "test_id"
        assert result.data == "test_data"
        
    finally:
        # 清理
        db_session.rollback()
        TestModel.__table__.drop(bind=db_session.bind, checkfirst=True) 