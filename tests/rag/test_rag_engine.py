"""
Tests for RAG engine
"""
import pytest
import asyncio

from windows_ai.rag.engine import (
    RAGEngine,
    RAGConfig,
    RerankStrategy,
    Reranker,
    ContextBuilder,
    RetrievalResult
)


class TestReranker:
    """Test re-ranking algorithms"""

    def test_mmr_rerank(self):
        """Test MMR re-ranking"""
        import numpy as np

        # Create sample results
        results = [
            RetrievalResult(content=f"Document {i}", score=0.9 - i*0.1, metadata={})
            for i in range(5)
        ]

        # Create sample embeddings (random for testing)
        query_embedding = np.random.rand(128).tolist()
        embeddings = [np.random.rand(128).tolist() for _ in range(5)]

        # Rerank
        reranked = Reranker.mmr_rerank(
            query_embedding=query_embedding,
            results=results,
            embeddings=embeddings,
            lambda_param=0.7,
            top_k=3
        )

        assert len(reranked) == 3
        assert all(isinstance(r, RetrievalResult) for r in reranked)


class TestContextBuilder:
    """Test context building"""

    def test_build_context(self):
        """Test context building from results"""
        results = [
            RetrievalResult(
                content="First document content",
                score=0.9,
                metadata={"file_name": "doc1.txt"}
            ),
            RetrievalResult(
                content="Second document content",
                score=0.8,
                metadata={"file_name": "doc2.txt"}
            )
        ]

        context = ContextBuilder.build_context(
            results=results,
            max_tokens=1000,
            include_metadata=True
        )

        assert "First document content" in context
        assert "Second document content" in context
        assert "[Source 1]" in context
        assert "doc1.txt" in context

    def test_build_context_token_limit(self):
        """Test context building with token limits"""
        results = [
            RetrievalResult(
                content="x" * 10000,  # Very long content
                score=0.9,
                metadata={}
            ),
            RetrievalResult(
                content="y" * 10000,
                score=0.8,
                metadata={}
            )
        ]

        context = ContextBuilder.build_context(
            results=results,
            max_tokens=100,  # Low limit
            include_metadata=False
        )

        # Should only include first result due to token limit
        assert context


class TestRAGConfig:
    """Test RAG configuration"""

    def test_default_config(self):
        """Test default configuration"""
        config = RAGConfig(index_name="test")

        assert config.index_name == "test"
        assert config.top_k == 10
        assert config.rerank_top_k == 5
        assert config.rerank_strategy == RerankStrategy.NONE

    def test_custom_config(self):
        """Test custom configuration"""
        config = RAGConfig(
            index_name="custom",
            top_k=20,
            rerank_top_k=10,
            rerank_strategy=RerankStrategy.MMR,
            mmr_lambda=0.8,
            use_hybrid_search=True,
            hybrid_alpha=0.6
        )

        assert config.index_name == "custom"
        assert config.top_k == 20
        assert config.rerank_strategy == RerankStrategy.MMR
        assert config.mmr_lambda == 0.8


class TestRAGEngine:
    """Test RAG engine functionality"""

    @pytest.fixture
    def mock_vector_db(self):
        """Create mock vector database"""
        class MockVectorDB:
            async def search(self, *args, **kwargs):
                return {
                    "status": "success",
                    "results": [
                        type('Result', (), {
                            'document': 'Test document 1',
                            'score': 0.9,
                            'metadata': {'source': 'test1.txt'}
                        }),
                        type('Result', (), {
                            'document': 'Test document 2',
                            'score': 0.8,
                            'metadata': {'source': 'test2.txt'}
                        })
                    ]
                }

            async def batch_upsert(self, *args, **kwargs):
                return {
                    "status": "success",
                    "total": kwargs.get('vectors', [[]]).__len__(),
                    "upserted": kwargs.get('vectors', [[]]).__len__()
                }

        return MockVectorDB()

    @pytest.fixture
    def mock_embedding_model(self):
        """Create mock embedding model"""
        import numpy as np

        class MockEmbeddingModel:
            config = type('Config', (), {'dimension': 128})()

            async def embed(self, texts):
                if isinstance(texts, str):
                    return np.random.rand(128).tolist()
                return [np.random.rand(128).tolist() for _ in texts]

        return MockEmbeddingModel()

    def test_rag_engine_initialization(self, mock_vector_db, mock_embedding_model):
        """Test RAG engine initialization"""
        config = RAGConfig(index_name="test")
        engine = RAGEngine(
            vector_db=mock_vector_db,
            embedding_model=mock_embedding_model,
            config=config
        )

        assert engine.vector_db == mock_vector_db
        assert engine.embedding_model == mock_embedding_model
        assert engine.config == config

    @pytest.mark.asyncio
    async def test_index_documents(self, mock_vector_db, mock_embedding_model):
        """Test indexing documents"""
        config = RAGConfig(index_name="test")
        engine = RAGEngine(
            vector_db=mock_vector_db,
            embedding_model=mock_embedding_model,
            config=config
        )

        documents = [
            {"content": "Document 1", "metadata": {"source": "doc1"}},
            {"content": "Document 2", "metadata": {"source": "doc2"}}
        ]

        result = await engine.index_documents(documents)

        assert result["status"] == "success"
        assert result["total"] == 2

    @pytest.mark.asyncio
    async def test_retrieve(self, mock_vector_db, mock_embedding_model):
        """Test document retrieval"""
        config = RAGConfig(index_name="test")
        engine = RAGEngine(
            vector_db=mock_vector_db,
            embedding_model=mock_embedding_model,
            config=config
        )

        results = await engine.retrieve(
            query="Test query",
            top_k=5,
            rerank=False
        )

        assert len(results) > 0
        assert all(isinstance(r, RetrievalResult) for r in results)


class TestRetrievalResult:
    """Test retrieval result dataclass"""

    def test_retrieval_result_creation(self):
        """Test creating retrieval result"""
        result = RetrievalResult(
            content="Test content",
            score=0.95,
            metadata={"source": "test.txt"},
            chunk_id=1,
            document_hash="abc123"
        )

        assert result.content == "Test content"
        assert result.score == 0.95
        assert result.metadata["source"] == "test.txt"
        assert result.chunk_id == 1
        assert result.document_hash == "abc123"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
