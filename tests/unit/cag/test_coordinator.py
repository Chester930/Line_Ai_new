import pytest
from src.shared.cag.coordinator import CAGCoordinator
from src.shared.cag.exceptions import CAGError
from src.shared.cag.state import DialogueState
from unittest.mock import AsyncMock
from typing import Dict, Any

@pytest.mark.asyncio
class TestCAGCoordinator:
    async def test_process_message(self, coordinator):
        """測試消息處理流程"""
        message = "What is Python?"
        context = {"user_id": "test_user"}
        
        response = await coordinator.process_message(message, context)
        assert response == "This is a mock response"
        
        state = await coordinator.state_tracker.get_current_state()
        assert state.state == DialogueState.ACTIVE

    async def test_error_handling(self, coordinator):
        """測試錯誤處理"""
        coordinator.rag_system.retrieve.side_effect = Exception("RAG error")
        
        with pytest.raises(CAGError) as exc_info:
            await coordinator.process_message("test", {})
        
        assert "RAG error" in str(exc_info.value)
        
        state = await coordinator.state_tracker.get_current_state()
        assert state.state == DialogueState.ERROR
        assert "RAG error" in state.metadata["error"]