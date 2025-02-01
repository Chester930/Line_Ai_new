from typing import Any, Dict, Optional
from pathlib import Path
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base
from sqlalchemy.pool import QueuePool
from sqlalchemy.exc import SQLAlchemyError
import logging

from ..utils.logger import logger

# 使用新的方式定義 Base
Base = declarative_base()

logger = logging.getLogger(__name__)

# 全局數據庫實例
db = None

def init_db():
    """初始化數據庫"""
    global db
    if db is None:
        db = Database()
    db.init_db()
    return db

def get_db():
    """獲取數據庫實例"""
    global db
    if db is None:
        db = Database()
    return db

class Database:
    """數據庫管理器"""
    _instance = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    def __init__(self, settings=None):
        if not hasattr(self, '_initialized'):
            self._engine = None
            self._session_factory = None
            self._settings = settings
            self._initialized = True
        
    def init_db(self):
        """初始化數據庫"""
        if not self._settings:
            # 延遲導入 settings
            from ..config import settings
            self._settings = settings
            
        try:
            self._engine = create_engine(
                self._settings.DATABASE_URL,
                echo=self._settings.DATABASE_ECHO,
                poolclass=QueuePool,
                pool_size=5,
                max_overflow=10
            )
            
            self._session_factory = sessionmaker(
                bind=self._engine,
                autocommit=False,
                autoflush=False
            )
            
            Base.metadata.create_all(self._engine)
            logger.info("數據庫初始化成功")
            
        except Exception as e:
            logger.error(f"數據庫初始化失敗: {str(e)}")
            raise

    def create_tables(self):
        """創建所有表"""
        try:
            Base.metadata.create_all(bind=self._engine)
            logger.info("數據庫表創建成功")
        except SQLAlchemyError as e:
            logger.error(f"創建數據庫表失敗: {str(e)}")
            raise
    
    def get_session(self):
        """獲取數據庫會話"""
        if not self._session_factory:
            raise RuntimeError("數據庫尚未初始化")
            
        session = self._session_factory()
        try:
            yield session
        except SQLAlchemyError as e:
            session.rollback()
            logger.error(f"數據庫錯誤: {str(e)}")
            raise
        finally:
            session.close() 