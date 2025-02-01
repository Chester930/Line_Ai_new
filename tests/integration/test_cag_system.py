import pytest
import asyncio
from pathlib import Path
import json
from unittest.mock import patch
from src.shared.cag.coordinator import CAGCoordinator
from src.shared.config.cag_config import ConfigManager
from src.shared.models.user import User
from src.shared.database import get_session
from src.shared.session.base import Message

class TestCAGSystem:
    @pytest.fixture(scope="class")
    def config_path(self, tmp_path_factory):
        """創建臨時配置文件"""
        config_dir = tmp_path_factory.mktemp("config")
        config_file = config_dir / "cag_config.json"
        
        test_config = {
            "max_context_length": 2000,
            "max_history_messages": 10,
            "memory_ttl": 3600,
            "max_memory_items": 1000,
            "enable_state_tracking": True,
            "max_state_history": 100,
            "default_model": "gemini",
            "log_level": "DEBUG",
            "models": {
                "gemini": {
                    "name": "gemini",
                    "api_key": "test_key",
                    "model_name": "gemini-pro",
                    "max_tokens": 1000,
                    "temperature": 0.7
                }
            }
        }
        
        config_file.write_text(json.dumps(test_config))
        return str(config_file)
    
    @pytest.fixture
    async def coordinator(self, config_path):
        """創建 CAG 協調器實例"""
        coordinator = CAGCoordinator(config_path=config_path)
        await coordinator.start()
        yield coordinator
        await coordinator.stop()
    
    @pytest.fixture
    async def test_user(self):
        """創建測試用戶"""
        async with get_session() as session:
            user = User(
                username="test_user",
                email="test@example.com",
                role="user"
            )
            session.add(user)
            await session.commit()
            return user
    
    @pytest.mark.asyncio
    async def test_system_startup(self, coordinator):
        """測試系統啟動"""
        assert coordinator.model is not None
        assert coordinator.context_manager is not None
        assert coordinator.memory_pool is not None
        assert coordinator.state_tracker is not None
        assert coordinator.session_manager is not None
        assert coordinator.plugin_manager is not None
    
    @pytest.mark.asyncio
    async def test_message_processing(self, coordinator, test_user):
        """測試消息處理"""
        # 發送測試消息
        result = await coordinator.process_message(
            message="Hello, AI!",
            user_id=test_user.id
        )
        
        assert result is not None
        assert isinstance(result.content, str)
        assert len(result.content) > 0
    
    @pytest.mark.asyncio
    async def test_session_management(self, coordinator, test_user):
        """測試會話管理"""
        # 創建新會話
        session = await coordinator.session_manager.create_session(test_user.id)
        assert session is not None
        
        # 添加消息到會話
        message = Message.create(
            user_id=test_user.id,
            content="Test message"
        )
        session.add_message(message)
        
        # 更新會話
        await coordinator.session_manager.update_session(session)
        
        # 獲取會話
        retrieved_session = await coordinator.session_manager.get_session(session.id)
        assert retrieved_session is not None
        assert len(retrieved_session.messages) == 1
    
    @pytest.mark.asyncio
    async def test_plugin_integration(self, coordinator):
        """測試插件整合"""
        # 載入測試插件
        await coordinator.plugin_manager.load_plugins()
        
        # 檢查插件狀態
        plugins = coordinator.plugin_manager.list_plugins()
        assert len(plugins) > 0
    
    @pytest.mark.asyncio
    async def test_model_switching(self, coordinator, test_user):
        """測試模型切換"""
        # 使用默認模型
        result1 = await coordinator.process_message(
            message="Test message 1",
            user_id=test_user.id
        )
        
        # 切換模型
        coordinator.system_config.default_model = "gpt"
        result2 = await coordinator.process_message(
            message="Test message 2",
            user_id=test_user.id
        )
        
        assert result1.model_info["model"] != result2.model_info["model"]
    
    @pytest.mark.asyncio
    async def test_error_handling(self, coordinator, test_user):
        """測試錯誤處理"""
        # 模擬模型錯誤
        with patch.object(coordinator.model, 'generate', side_effect=Exception("Test error")):
            with pytest.raises(Exception):
                await coordinator.process_message(
                    message="Test message",
                    user_id=test_user.id
                )
    
    @pytest.mark.asyncio
    async def test_memory_management(self, coordinator, test_user):
        """測試記憶管理"""
        # 添加記憶
        await coordinator.memory_pool.add_memory(
            f"context_{test_user.id}",
            [{"role": "user", "content": "Test memory"}],
            ttl=60
        )
        
        # 獲取記憶
        memory = await coordinator.memory_pool.get_memory(f"context_{test_user.id}")
        assert memory is not None
        assert len(memory) == 1
    
    @pytest.mark.asyncio
    async def test_state_tracking(self, coordinator, test_user):
        """測試狀態追踪"""
        # 更新狀態
        await coordinator.state_tracker.set_state(
            "ACTIVE",
            metadata={"user_id": test_user.id}
        )
        
        # 獲取狀態
        state = await coordinator.state_tracker.get_state()
        assert state.name == "ACTIVE"
        assert state.metadata["user_id"] == test_user.id 