import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from src.shared.database.base import Base

@pytest.fixture(scope="function")
def engine():
    """創建測試數據庫引擎"""
    # 使用 SQLite 內存數據庫進行測試
    engine = create_engine("sqlite:///:memory:")
    return engine

@pytest.fixture(scope="function")
def session(engine):
    """提供測試數據庫會話"""
    # 創建所有表
    Base.metadata.create_all(engine)
    
    # 創建會話
    Session = sessionmaker(bind=engine)
    session = Session()
    
    try:
        yield session
    finally:
        session.close()
        # 清理數據庫
        Base.metadata.drop_all(engine) 