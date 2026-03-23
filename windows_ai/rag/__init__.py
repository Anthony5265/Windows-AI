"""
RAG (Retrieval-Augmented Generation) Framework
Document processing, chunking, embedding, hybrid search, and file indexing
"""
from typing import Dict, Any, List, Optional
import logging

# Import main components
from .engine import (
    RAGEngine,
    RAGConfig,
    RAGResponse,
    RetrievalResult,
    RerankStrategy,
    Reranker,
    ContextBuilder
)

from .document_processor import (
    RAGDocumentProcessor,
    DocumentProcessor,
    ChunkConfig,
    ChunkStrategy,
    Document,
    DocumentChunk,
    FileReader,
    FileType,
    TextChunker,
)

from .hybrid_search import (
    BM25Index,
    VectorIndex,
    HybridSearch,
    SearchResult,
)

from .file_indexer import (
    FileSystemIndexer,
)

logger = logging.getLogger(__name__)

__all__ = [
    "RAGEngine",
    "RAGConfig",
    "RAGResponse",
    "RetrievalResult",
    "RerankStrategy",
    "Reranker",
    "ContextBuilder",
    "RAGDocumentProcessor",
    "DocumentProcessor",
    "ChunkConfig",
    "ChunkStrategy",
    "Document",
    "DocumentChunk",
    "FileReader",
    "FileType",
    "TextChunker",
    "BM25Index",
    "VectorIndex",
    "HybridSearch",
    "SearchResult",
    "FileSystemIndexer",
]
