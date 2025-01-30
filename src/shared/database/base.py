from typing import Any, Dict, Optional
from pathlib import Path
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base
from sqlalchemy.pool import QueuePool
from sqlalchemy.exc import SQLAlchemyError

from ..config import settings  # 更新引用路徑
from ..utils.logger import logger

# 使用新的方式定義 Base
Base = declarative_base()

# 創建數據庫引擎
engine = create_engine(
    settings.DATABASE_URL,
    echo=settings.DATABASE_ECHO,
    poolclass=QueuePool,
    pool_size=5,
    max_overflow=10
)

# 創建會話工廠
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def init_db():
    """初始化數據庫"""
    Base.metadata.create_all(bind=engine)

def get_db():
    """獲取數據庫會話"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

class Database:
    """數據庫管理器"""
    _instance = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    def __init__(self):
        if not hasattr(self, 'initialized'):
            self.engine = create_engine(settings.DATABASE_URL, echo=settings.DATABASE_ECHO)
            self.SessionLocal = sessionmaker(bind=self.engine)
            self.initialized = True
    
    def create_tables(self):
        """創建所有表"""
        try:
            Base.metadata.create_all(bind=self.engine)
            logger.info("數據庫表創建成功")
        except SQLAlchemyError as e:
            logger.error(f"創建數據庫表失敗: {str(e)}")
            raise
    
    def get_session(self):
        """獲取數據庫會話"""
        session = self.SessionLocal()
        try:
            yield session
        except SQLAlchemyError as e:
            session.rollback()
            logger.error(f"數據庫錯誤: {str(e)}")
            raise
        finally:
            session.close()

# 創建全局數據庫實例
db = Database() 