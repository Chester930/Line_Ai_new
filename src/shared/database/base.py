from typing import Any, Dict, Optional
from pathlib import Path
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base
from sqlalchemy.pool import QueuePool, NullPool
from sqlalchemy.exc import SQLAlchemyError
import logging
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
import os
from sqlalchemy.sql import text
from contextlib import asynccontextmanager
from typing import AsyncGenerator

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
    _initialized = False
    
    def __new__(cls, url: str = None):
        if not cls._instance:
            instance = super().__new__(cls)
            instance.url = url or os.getenv('DATABASE_URL')
            if not instance.url:
                raise ValueError("Database URL not provided")
            instance.engine = create_async_engine(
                instance.url,
                echo=False,
                future=True
            )
            instance._session_factory = sessionmaker(
                instance.engine,
                class_=AsyncSession,
                expire_on_commit=False
            )
            instance._initialized = True
            cls._instance = instance
        return cls._instance
    
    def __init__(self, url: str = None):
        """初始化時不做任何操作"""
        pass
        
    @property
    def initialized(self):
        """檢查是否已初始化"""
        return self._initialized
        
    async def create_tables(self):
        """創建所有表"""
        if not self.initialized:
            # 重新初始化引擎和會話工廠
            self.engine = create_async_engine(
                self.url,
                echo=False,
                future=True
            )
            self._session_factory = sessionmaker(
                self.engine,
                class_=AsyncSession,
                expire_on_commit=False
            )
            
        # 確保所有模型都被導入
        from .models import User, Conversation
        
        async with self.engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
            
        self._initialized = True
        
    async def drop_tables(self):
        """刪除所有表"""
        if not self.initialized:
            raise RuntimeError("Database not initialized")
            
        # 確保所有模型都被導入
        from .models import User, Conversation
        
        async with self.engine.begin() as conn:
            await conn.run_sync(Base.metadata.drop_all)
            
        # 重置初始化狀態，但保留引擎和會話工廠
        self._initialized = False
        
    @asynccontextmanager
    async def session(self) -> AsyncGenerator[AsyncSession, None]:
        """獲取數據庫會話的上下文管理器"""
        if not self.initialized:
            raise RuntimeError("Database not initialized")
            
        async with self._session_factory() as session:
            try:
                yield session
            except Exception as e:
                await session.rollback()
                raise
            finally:
                await session.close()
        
    @property
    def async_session(self):
        if self._session_factory is None:
            raise RuntimeError("Database not initialized")
        return self._session_factory
        
    async def test_connection(self):
        """測試數據庫連接"""
        try:
            async with self.engine.begin() as conn:
                await conn.execute(text("SELECT 1"))
            return True
        except Exception as e:
            logger.error(f"Database connection test failed: {e}")
            return False
            
    async def close(self):
        """關閉數據庫連接"""
        if self.engine:
            await self.engine.dispose()
            self.engine = None
            self._session_factory = None
            self._initialized = False
            type(self)._instance = None  # 重置單例
            
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