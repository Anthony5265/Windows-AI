"""
RAG Document Processor

Provides document processing capabilities within the RAG pipeline,
including file reading, text chunking, and metadata extraction.

This module re-exports the core document processing components from
``windows_ai.document_processor`` and adds RAG-specific processing
utilities such as batch processing and query-aware chunking.
"""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from ..document_processor import (
    ChunkConfig,
    ChunkStrategy,
    Document,
    DocumentChunk,
    DocumentProcessor,
    FileReader,
    FileType,
    TextChunker,
)

logger = logging.getLogger(__name__)

# Re-export core classes so consumers can import from windows_ai.rag
__all__ = [
    "ChunkConfig",
    "ChunkStrategy",
    "Document",
    "DocumentChunk",
    "DocumentProcessor",
    "FileReader",
    "FileType",
    "TextChunker",
    "RAGDocumentProcessor",
]


class RAGDocumentProcessor:
    """Extended document processor with RAG-specific capabilities.

    Wraps :class:`DocumentProcessor` and adds batch processing helpers,
    metadata enrichment for retrieval, and chunk-ID generation suitable
    for vector-database indexing.

    Args:
        chunk_config: Optional chunking configuration. Uses defaults if
            not provided.

    Example::

        processor = RAGDocumentProcessor()
        chunks = processor.process_files_for_indexing(
            ["/docs/readme.md", "/docs/guide.txt"]
        )
        # chunks is a list of dicts ready for RAGEngine.index_documents()
    """

    def __init__(self, chunk_config: Optional[ChunkConfig] = None) -> None:
        self.chunk_config = chunk_config or ChunkConfig()
        self._processor = DocumentProcessor(self.chunk_config)

    def process_text(
        self,
        text: str,
        metadata: Optional[Dict[str, Any]] = None,
        source: str = "inline",
    ) -> List[Dict[str, Any]]:
        """Chunk raw text and return documents ready for indexing.

        Args:
            text: The raw text to process.
            metadata: Optional metadata to attach to every chunk.
            source: A label identifying the origin of the text.

        Returns:
            A list of dictionaries with ``content`` and ``metadata`` keys,
            suitable for passing to :meth:`RAGEngine.index_documents`.
        """
        chunker = TextChunker(self.chunk_config)
        doc = Document(
            content=text,
            metadata=metadata or {},
            file_path=None,
            file_type=FileType.TXT,
        )
        chunks = chunker.chunk(text, doc)
        result: List[Dict[str, Any]] = []
        for idx, chunk in enumerate(chunks):
            chunk_meta = {
                **(metadata or {}),
                "source": source,
                "chunk_index": idx,
                "total_chunks": len(chunks),
                "document_hash": doc.hash,
                "start_char": chunk.start_char,
                "end_char": chunk.end_char,
            }
            result.append({"content": chunk.content, "metadata": chunk_meta})
        return result

    def process_file_for_indexing(
        self, file_path: str
    ) -> List[Dict[str, Any]]:
        """Process a single file and return chunks ready for indexing.

        Args:
            file_path: Path to the file to process.

        Returns:
            A list of chunk dictionaries with ``content`` and ``metadata``
            keys.

        Raises:
            FileNotFoundError: If *file_path* does not exist.
            ValueError: If the file cannot be read.
        """
        path = Path(file_path)
        if not path.exists():
            raise FileNotFoundError(f"File not found: {file_path}")

        try:
            doc, chunks = self._processor.process_file(file_path)
        except Exception as exc:
            logger.error("Failed to process file %s: %s", file_path, exc)
            raise ValueError(f"Could not process {file_path}: {exc}") from exc

        result: List[Dict[str, Any]] = []
        for idx, chunk in enumerate(chunks):
            chunk_meta = {
                **chunk.metadata,
                "source": str(path),
                "file_name": path.name,
                "file_type": doc.file_type.value if doc.file_type else "unknown",
                "chunk_index": idx,
                "total_chunks": len(chunks),
                "document_hash": doc.hash,
                "start_char": chunk.start_char,
                "end_char": chunk.end_char,
            }
            result.append({"content": chunk.content, "metadata": chunk_meta})

        logger.info(
            "Processed %s into %d chunks", path.name, len(result)
        )
        return result

    def process_files_for_indexing(
        self,
        file_paths: List[str],
        *,
        skip_errors: bool = True,
    ) -> List[Dict[str, Any]]:
        """Batch-process multiple files for indexing.

        Args:
            file_paths: Paths to files to process.
            skip_errors: When ``True`` (default), files that fail to
                process are logged and skipped rather than raising.

        Returns:
            Combined list of chunk dictionaries from all files.
        """
        all_chunks: List[Dict[str, Any]] = []
        for fp in file_paths:
            try:
                all_chunks.extend(self.process_file_for_indexing(fp))
            except Exception as exc:
                if skip_errors:
                    logger.warning("Skipping %s: %s", fp, exc)
                else:
                    raise
        logger.info(
            "Batch processed %d files into %d total chunks",
            len(file_paths),
            len(all_chunks),
        )
        return all_chunks

    def process_directory_for_indexing(
        self,
        directory: str,
        *,
        recursive: bool = True,
        file_patterns: Optional[List[str]] = None,
    ) -> List[Dict[str, Any]]:
        """Process an entire directory for RAG indexing.

        Args:
            directory: Path to the directory.
            recursive: Whether to recurse into subdirectories.
            file_patterns: Optional glob patterns to filter files
                (e.g. ``["*.md", "*.txt"]``).

        Returns:
            Combined list of chunk dictionaries from all matched files.
        """
        dir_path = Path(directory)
        if not dir_path.is_dir():
            raise NotADirectoryError(f"Not a directory: {directory}")

        try:
            results = self._processor.process_directory(
                directory, recursive=recursive, file_patterns=file_patterns
            )
        except Exception as exc:
            logger.error("Failed to process directory %s: %s", directory, exc)
            raise

        all_chunks: List[Dict[str, Any]] = []
        for doc, chunks in results:
            for idx, chunk in enumerate(chunks):
                chunk_meta = {
                    **chunk.metadata,
                    "source": doc.file_path or directory,
                    "file_type": doc.file_type.value if doc.file_type else "unknown",
                    "chunk_index": idx,
                    "total_chunks": len(chunks),
                    "document_hash": doc.hash,
                    "start_char": chunk.start_char,
                    "end_char": chunk.end_char,
                }
                all_chunks.append({"content": chunk.content, "metadata": chunk_meta})

        logger.info(
            "Processed directory %s: %d documents, %d total chunks",
            directory,
            len(results),
            len(all_chunks),
        )
        return all_chunks
