import pytest
from datetime import datetime, timedelta
import asyncio
from src.shared.session.manager import SessionManager
from src.shared.session.base import Message

@pytest.fixture
def session_config():
    return {
        "session_timeout": 3600,
        "cleanup_interval": 300,
        "max_sessions": 1000
    }

@pytest.fixture
async def session_manager(session_config):
    manager = SessionManager(session_config)
    await manager.start()
    yield manager
    await manager.stop()

class TestSessionManager:
    async def test_create_session(self, session_manager):
        session = await session_manager.create_session("test_user_1")
        assert session is not None
        assert session.id in session_manager.sessions
    
    async def test_get_session(self, session_manager):
        session = await session_manager.create_session("test_user_2")
        retrieved = await session_manager.get_session(session.id)
        assert retrieved is not None
        assert retrieved.id == session.id
    
    async def test_expired_session(self, session_manager):
        session = await session_manager.create_session("test_user_3")
        session.last_activity = datetime.now() - timedelta(seconds=session.ttl + 1)
        retrieved = await session_manager.get_session(session.id)
        assert retrieved is None
    
    async def test_update_session(self, session_manager):
        session = await session_manager.create_session("test_user_4")
        session.data["test"] = "value"
        success = await session_manager.update_session(session)
        assert success
        
        updated = await session_manager.get_session(session.id)
        assert updated.data["test"] == "value"
    
    async def test_cleanup_expired(self, session_manager):
        # 創建一些過期會話
        for i in range(3):
            session = await session_manager.create_session(f"test_user_{i}")
            session.last_activity = datetime.now() - timedelta(seconds=session.ttl + 1)
        
        cleaned = await session_manager.cleanup_expired()
        assert cleaned == 3
        assert len(session_manager.sessions) == 0 