import pytest
from datetime import datetime, timedelta
from src.shared.chat.memory import MemoryManager, Memory

@pytest.fixture
def memory_manager():
    return MemoryManager(capacity=5)

def test_memory_addition(memory_manager):
    """測試記憶添加"""
    memory_manager.add_memory("測試記憶", importance=0.8)
    assert len(memory_manager.memories) == 1
    assert memory_manager.memories[0].content == "測試記憶"
    assert memory_manager.memories[0].importance == 0.8

def test_capacity_limit(memory_manager):
    """測試容量限制"""
    for i in range(10):
        memory_manager.add_memory(f"記憶 {i}", importance=0.1)
    
    assert len(memory_manager.memories) == 5
    assert memory_manager.memories[-1].content == "記憶 9"

def test_importance_based_cleanup(memory_manager):
    """測試基於重要性的清理"""
    # 添加重要記憶
    memory_manager.add_memory("重要記憶", importance=0.9)
    
    # 添加普通記憶
    for i in range(5):
        memory_manager.add_memory(f"普通記憶 {i}", importance=0.1)
    
    assert len(memory_manager.memories) == 5
    assert any(m.content == "重要記憶" for m in memory_manager.memories)

def test_relevant_memories_retrieval(memory_manager):
    """測試相關記憶檢索"""
    memory_manager.add_memory("記憶1", importance=0.8)
    memory_manager.add_memory("記憶2", importance=0.3)
    memory_manager.add_memory("記憶3", importance=0.9)
    
    memories = memory_manager.get_relevant_memories("測試", min_importance=0.5)
    assert len(memories) == 2
    assert all(m.importance >= 0.5 for m in memories)

def test_old_memories_cleanup(memory_manager):
    """測試舊記憶清理"""
    # 添加舊記憶
    old_memory = Memory(
        content="舊記憶",
        importance=0.3,
        timestamp=datetime.now() - timedelta(days=40)
    )
    memory_manager.memories.append(old_memory)
    
    # 添加新記憶
    memory_manager.add_memory("新記憶", importance=0.4)
    
    memory_manager.clear_old_memories(days=30)
    assert len(memory_manager.memories) == 1
    assert memory_manager.memories[0].content == "新記憶" 