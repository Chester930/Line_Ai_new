import pytest
from src.shared.rag.system import RAGSystem

@pytest.mark.asyncio
class TestRAGSystem:
    @pytest.fixture
    async def rag_system(self):
        return RAGSystem()
    
    async def test_add_document(self, rag_system):
        """測試添加文檔"""
        success = await rag_system.add_document(
            "Python is a programming language."
        )
        assert success
        assert len(rag_system.documents) == 1
    
    async def test_retrieve(self, rag_system):
        """測試文檔檢索"""
        # 添加測試文檔
        await rag_system.add_document(
            "Python is a programming language."
        )
        await rag_system.add_document(
            "Java is another programming language."
        )
        
        # 測試檢索
        results = await rag_system.retrieve("Python")
        assert len(results) == 1
        assert "Python" in results[0] 