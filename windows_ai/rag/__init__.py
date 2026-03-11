"""
RAG (Retrieval-Augmented Generation) Framework
Document processing, chunking, embedding, and semantic search
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
]
