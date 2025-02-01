import pytest
from datetime import datetime, timedelta
import asyncio
from src.shared.session.manager import SessionManager
from src.shared.session.base import Message

class TestSessionManager:
    @pytest.fixture
    async def session_manager(self):
        manager = SessionManager()
        await manager.start()
        yield manager
        await manager.stop()
    
    async def test_create_session(self, session_manager):
        session = await session_manager.create_session("test_user")
        assert session.user_id == "test_user"
        assert session.id in session_manager.sessions
    
    async def test_get_session(self, session_manager):
        session = await session_manager.create_session("test_user")
        retrieved = await session_manager.get_session(session.id)
        assert retrieved == session
    
    async def test_expired_session(self, session_manager):
        session = await session_manager.create_session("test_user", ttl=1)
        await asyncio.sleep(1.1)
        retrieved = await session_manager.get_session(session.id)
        assert retrieved is None
    
    async def test_update_session(self, session_manager):
        session = await session_manager.create_session("test_user")
        message = Message.create(
            user_id="test_user",
            content="Hello",
            role="user"
        )
        session.add_message(message)
        success = await session_manager.update_session(session)
        assert success
        
        updated = await session_manager.get_session(session.id)
        assert len(updated.messages) == 1
    
    async def test_cleanup_expired(self, session_manager):
        # 創建一些會話，包括過期的
        await session_manager.create_session("user1", ttl=1)
        await session_manager.create_session("user2", ttl=3600)
        
        await asyncio.sleep(1.1)
        expired_count = await session_manager.cleanup_expired()
        assert expired_count == 1
        assert len(session_manager.sessions) == 1 