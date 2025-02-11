import pytest
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import NullPool, StaticPool
from src.shared.database.base import Base, Database
from src.shared.database.models.user import User
from src.shared.database.models.conversation import Conversation
from datetime import datetime
import os
from sqlalchemy import text
from sqlalchemy import select
from sqlalchemy.orm import selectinload

# 設置測試環境變數
os.environ['DATABASE_URL'] = "sqlite+aiosqlite://"  # 使用共享記憶體數據庫

@pytest.fixture(scope="function")
async def database():
    """提供數據庫實例"""
    # 確保每次測試都使用新的數據庫實例
    Database._instance = None
    Database._initialized = False
    
    db = Database(url="sqlite+aiosqlite:///:memory:")
    assert db.initialized
    await db.create_tables()
    yield db
    await db.drop_tables()
    await db.close()

@pytest.fixture(scope="function")
async def test_session(database):
    """提供測試會話"""
    async with database.session() as session:
        yield session
        await session.rollback()

class TestDatabase:
    @pytest.fixture(scope="function")
    async def db(self):
        """數據庫測試夾具"""
        # 重置數據庫單例
        Database._instance = None
        Database._initialized = False
        
        database = Database(url="sqlite+aiosqlite:///:memory:")
        assert database.initialized
        await database.create_tables()
        yield database
        await database.drop_tables()
        await database.close()
        
    @pytest.mark.asyncio
    async def test_singleton_behavior(self, db):
        """測試單例模式"""
        db2 = Database(url="sqlite+aiosqlite:///:memory:")
        assert db is db2  # 應該是同一個實例
        assert db.url == db2.url
        
    @pytest.mark.asyncio
    async def test_initialization(self, db):
        """測試初始化"""
        assert db.initialized
        assert db.engine is not None
        assert db._session_factory is not None
        
    @pytest.mark.asyncio
    async def test_session_management(self, db):
        """測試會話管理"""
        async with db.session() as session:
            # 測試基本操作
            user = User(line_id="test_user")
            session.add(user)
            await session.commit()
            
            # 測試回滾
            user2 = User(line_id="test_user")  # 重複的 line_id
            session.add(user2)
            with pytest.raises(Exception):
                await session.commit()
            await session.rollback()
            
    @pytest.mark.asyncio
    async def test_error_handling(self, db):
        """測試錯誤處理"""
        async with db.session() as session:
            with pytest.raises(Exception):
                # 故意製造錯誤
                await session.execute("INVALID SQL")
                await session.commit()

    @pytest.mark.asyncio
    async def test_create_user(self, database):
        """測試創建用戶"""
        async with database.session() as session:
            user = User(
                line_id="test_user",
                name="Test User",  # 可選
                display_name="Test Display"  # 可選
            )
            session.add(user)
            await session.commit()
            
            result = await session.get(User, user.id)
            assert result is not None
            assert result.line_id == "test_user"
            
    @pytest.mark.asyncio
    async def test_create_conversation(self, db):
        """測試創建對話"""
        async with db.session() as session:
            # 創建用戶
            user = User(line_id="test_user")
            session.add(user)
            await session.commit()
            
            # 創建對話
            conversation = Conversation(
                user_id=user.id,
                content="Hello",
                role="user"
            )
            session.add(conversation)
            await session.commit()
            
            result = await session.get(Conversation, conversation.id)
            assert result is not None
            assert result.content == "Hello"
            
    @pytest.mark.asyncio
    async def test_transaction_rollback(self, db):
        """測試事務回滾"""
        async with db.session() as session:
            try:
                # 創建用戶
                user = User(line_id="test_user")
                session.add(user)
                
                # 故意製造錯誤
                invalid_conversation = Conversation(
                    user_id=999,  # 不存在的用戶ID
                    message="Should fail"
                )
                session.add(invalid_conversation)
                await session.commit()
            except:
                await session.rollback()
                
            # 驗證回滾 - 使用 text() 函數
            result = await session.execute(
                text("SELECT COUNT(*) FROM users")
            )
            count = result.scalar()
            assert count == 0

    @pytest.fixture(autouse=True)
    async def setup_database(self, database, test_session):
        """設置測試資料庫"""
        self.db = database
        self.engine = database.engine
        self.async_session = database.async_session
        self.session = test_session
        yield

    @pytest.mark.asyncio
    async def test_connection(self):
        """測試資料庫連接"""
        assert await self.db.test_connection()
        
    @pytest.mark.asyncio
    async def test_user_crud(self):
        """測試用戶 CRUD 操作"""
        # Create
        user = User(
            line_id="test_user_id",
            name="Test User",
            created_at=datetime.now()
        )
        self.session.add(user)
        await self.session.commit()
        
        # Read
        result = await self.session.get(User, user.id)
        assert result is not None
        assert result.line_id == "test_user_id"
        assert result.name == "Test User"
        
        # Update
        user.name = "Updated User"
        await self.session.commit()
        updated_user = await self.session.get(User, user.id)
        assert updated_user.name == "Updated User"
        
        # Delete
        await self.session.delete(user)
        await self.session.commit()
        deleted_user = await self.session.get(User, user.id)
        assert deleted_user is None
            
    @pytest.mark.asyncio
    async def test_conversation_crud(self):
        """測試對話 CRUD 操作"""
        async with self.async_session() as session:
            # 先創建用戶
            user = User(
                line_id="test_user_id",
                name="Test User",
                created_at=datetime.now()
            )
            session.add(user)
            await session.commit()
            
            # Create conversation
            conversation = Conversation(
                user_id=user.id,
                content="Test message",
                role="user",
                created_at=datetime.now()
            )
            session.add(conversation)
            await session.commit()
            
            # Read
            result = await session.get(Conversation, conversation.id)
            assert result is not None
            assert result.content == "Test message"
            assert result.role == "user"
            
            # Update
            conversation.content = "Updated message"
            await session.commit()
            updated_conv = await session.get(Conversation, conversation.id)
            assert updated_conv.content == "Updated message"
            
            # Delete
            await session.delete(conversation)
            await session.commit()
            deleted_conv = await session.get(Conversation, conversation.id)
            assert deleted_conv is None
            
    @pytest.mark.asyncio
    async def test_user_conversations_relationship(self):
        """測試用戶與對話的關聯關係"""
        async with self.async_session() as session:
            # 創建用戶
            user = User(
                line_id="test_user_id",
                name="Test User",
                created_at=datetime.now()
            )
            session.add(user)
            await session.commit()
            
            # 創建多個對話
            conversations = [
                Conversation(
                    user_id=user.id,
                    content=f"Message {i}",
                    role="user",
                    created_at=datetime.now()
                )
                for i in range(3)
            ]
            session.add_all(conversations)
            await session.commit()
            
            # 驗證關聯 - 使用 select 語句
            stmt = select(User).options(selectinload(User.conversations)).where(User.id == user.id)
            result = await session.execute(stmt)
            user_with_convs = result.scalar_one()
            
            assert len(user_with_convs.conversations) == 3
            assert all(conv.user_id == user.id for conv in user_with_convs.conversations)
            
    @pytest.mark.asyncio
    async def test_cascade_delete(self):
        """測試級聯刪除"""
        async with self.async_session() as session:
            # 創建用戶和對話
            user = User(
                line_id="test_user_id",
                name="Test User",
                created_at=datetime.now()
            )
            session.add(user)
            await session.commit()
            
            conversation = Conversation(
                user_id=user.id,
                content="Test message",
                role="user",
                created_at=datetime.now()
            )
            session.add(conversation)
            await session.commit()
            
            # 刪除用戶，對話應該也被刪除
            await session.delete(user)
            await session.commit()
            
            # 驗證對話也被刪除
            deleted_conv = await session.get(Conversation, conversation.id)
            assert deleted_conv is None

    @pytest.mark.asyncio
    async def test_database_initialization(self, db):
        """測試數據庫初始化"""
        assert db.initialized
        assert db.engine is not None
        assert db._session_factory is not None
        
        # 測試重複初始化
        db2 = Database(url="sqlite+aiosqlite:///:memory:")
        assert db2 is db  # 應該是同一個實例
        
    @pytest.mark.asyncio
    async def test_database_cleanup(self, db):
        """測試數據庫清理"""
        # 創建一些測試數據
        async with db.session() as session:
            user = User(line_id="test_user")
            session.add(user)
            await session.commit()
            
            # 驗證數據已創建
            result = await session.execute(text("SELECT COUNT(*) FROM users"))
            count = result.scalar()
            assert count == 1
            
        # 清理數據庫
        await db.drop_tables()
        
        # 重新創建表
        await db.create_tables()
        
        # 驗證清理結果
        async with db.session() as session:
            result = await session.execute(text("SELECT COUNT(*) FROM users"))
            count = result.scalar()
            assert count == 0 