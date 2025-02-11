import pytest
from src.shared.chat.context import ContextManager
from src.shared.chat.session import Message

@pytest.fixture
def context_manager():
    """創建上下文管理器"""
    return ContextManager(max_tokens=10)

@pytest.fixture
def sample_messages():
    """創建測試消息列表"""
    return [
        Message(content="第一條消息", role="user"),
        Message(content="第二條消息", role="assistant"),
        Message(content="第三條消息", role="user")
    ]

def test_context_trimming(context_manager, sample_messages):
    """測試上下文裁剪"""
    trimmed = context_manager.trim_context(sample_messages.copy())
    assert len(trimmed) < len(sample_messages)
    
    # 確保總token數不超過限制
    total_tokens = sum(len(msg.content.split()) for msg in trimmed)
    assert total_tokens <= context_manager.max_tokens

def test_key_information_extraction(context_manager, sample_messages):
    """測試關鍵信息提取"""
    info = context_manager.extract_key_information(sample_messages)
    
    assert 'user_intent' in info
    assert 'key_topics' in info
    assert 'sentiment' in info
    assert isinstance(info['key_topics'], list)

def test_empty_context(context_manager):
    """測試空上下文處理"""
    empty_messages = []
    
    trimmed = context_manager.trim_context(empty_messages)
    assert trimmed == []
    
    info = context_manager.extract_key_information(empty_messages)
    assert info['user_intent'] == "unknown"
    assert info['key_topics'] == []
    assert info['sentiment'] == "neutral"

def test_large_context(context_manager):
    """測試大量消息處理"""
    large_messages = [
        Message(content=f"消息 {i}", role="user")
        for i in range(20)
    ]
    
    trimmed = context_manager.trim_context(large_messages)
    assert len(trimmed) < len(large_messages)
    
    total_tokens = sum(len(msg.content.split()) for msg in trimmed)
    assert total_tokens <= context_manager.max_tokens 