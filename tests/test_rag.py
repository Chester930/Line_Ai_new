import pytest
from src.shared.rag import RAGSystem
from src.shared.rag.processor import DocumentProcessor
from src.shared.rag.store import VectorStore

class TestRAGSystem:
    @pytest.mark.asyncio
    async def test_document_processing(self):
        """Test document processing"""
        processor = DocumentProcessor()
        result = await processor.process("test document")
        assert result.chunks is not None
        assert len(result.chunks) > 0
        
    @pytest.mark.asyncio
    async def test_vector_store(self):
        """Test vector storage operations"""
        store = VectorStore()
        vectors = [(1, [0.1, 0.2, 0.3])]
        await store.store(vectors)
        results = await store.search([0.1, 0.2, 0.3], k=1)
        assert len(results) == 1
        
    @pytest.mark.asyncio
    async def test_retrieval(self):
        """Test document retrieval"""
        rag = RAGSystem()
        results = await rag.retrieve("test query")
        assert results is not None
        assert len(results) > 0 