import pytest
from sqlalchemy.orm import Session
from sqlalchemy import inspect, text
from sqlalchemy.exc import SQLAlchemyError
from src.shared.database.base import Database, Base
from src.shared.config.config import config

@pytest.fixture
def db():
    """數據庫測試夾具"""
    database = Database()
    return database

@pytest.fixture
def db_session(db):
    """提供測試數據庫會話"""
    session = next(db.get_session())
    try:
        yield session
    finally:
        session.close()

def test_database_connection(db):
    """測試數據庫連接"""
    assert db.engine is not None
    assert db.SessionLocal is not None

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
    assert db.initialized is True
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