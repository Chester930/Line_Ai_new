from typing import Any, Dict, Optional
from pathlib import Path
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, DeclarativeBase
from sqlalchemy.pool import QueuePool
from sqlalchemy.exc import SQLAlchemyError

from ..config.config import config, Settings
from ..utils.logger import logger

# 使用新的方式定義 Base
class Base(DeclarativeBase):
    pass

# 創建數據庫引擎
engine = create_engine(
    config.settings.database_url,
    echo=config.settings.database_echo,
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
            self.engine = create_engine(
                config.settings.database_url,
                echo=config.settings.database_echo
            )
            self.SessionLocal = sessionmaker(
                autocommit=False,
                autoflush=False,
                bind=self.engine
            )
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