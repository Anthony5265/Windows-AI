"""
Tests for the RAG document processor module.
"""

import os
import pytest
import tempfile
from pathlib import Path

from windows_ai.rag.document_processor import (
    RAGDocumentProcessor,
    ChunkConfig,
    ChunkStrategy,
    Document,
    DocumentChunk,
    FileReader,
    FileType,
    TextChunker,
)


class TestRAGDocumentProcessorImports:
    """Verify that re-exports from windows_ai.rag work."""

    def test_import_from_rag_package(self):
        """All document processing classes should be importable from windows_ai.rag."""
        from windows_ai.rag import (
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
        assert RAGDocumentProcessor is not None
        assert DocumentProcessor is not None
        assert ChunkConfig is not None

    def test_chunk_strategy_enum(self):
        """ChunkStrategy enum should have expected values."""
        assert ChunkStrategy.FIXED_SIZE.value == "fixed_size"
        assert ChunkStrategy.SEMANTIC.value == "semantic"
        assert ChunkStrategy.SENTENCE.value == "sentence"
        assert ChunkStrategy.PARAGRAPH.value == "paragraph"
        assert ChunkStrategy.SLIDING_WINDOW.value == "sliding_window"

    def test_file_type_enum(self):
        """FileType enum should have expected values."""
        assert FileType.TXT.value == "txt"
        assert FileType.PDF.value == "pdf"
        assert FileType.MD.value == "md"
        assert FileType.JSON.value == "json"


class TestRAGDocumentProcessor:
    """Tests for RAGDocumentProcessor."""

    @pytest.fixture
    def processor(self):
        """Create a default RAG document processor."""
        return RAGDocumentProcessor()

    @pytest.fixture
    def small_chunk_processor(self):
        """Create a processor with small chunk sizes for testing."""
        config = ChunkConfig(
            strategy=ChunkStrategy.FIXED_SIZE,
            chunk_size=50,
            chunk_overlap=10,
            min_chunk_size=10,
        )
        return RAGDocumentProcessor(chunk_config=config)

    def test_init_default_config(self, processor):
        """Default processor should have default chunk config."""
        assert processor.chunk_config is not None
        assert processor.chunk_config.strategy == ChunkStrategy.FIXED_SIZE

    def test_init_custom_config(self, small_chunk_processor):
        """Custom config should be stored."""
        assert small_chunk_processor.chunk_config.chunk_size == 50

    def test_process_text_basic(self, processor):
        """process_text should return list of chunk dicts."""
        # Text must exceed min_chunk_size (default 100 chars)
        text = "Hello world. " * 20  # ~260 chars
        result = processor.process_text(text)
        assert isinstance(result, list)
        assert len(result) >= 1
        for chunk in result:
            assert "content" in chunk
            assert "metadata" in chunk
            assert isinstance(chunk["content"], str)
            assert isinstance(chunk["metadata"], dict)

    def test_process_text_metadata(self, processor):
        """process_text should include provided metadata in chunks."""
        text = "Some text content for testing. " * 10  # ~300 chars
        meta = {"author": "test", "category": "unit-test"}
        result = processor.process_text(text, metadata=meta, source="test-input")
        assert len(result) >= 1
        chunk_meta = result[0]["metadata"]
        assert chunk_meta["author"] == "test"
        assert chunk_meta["category"] == "unit-test"
        assert chunk_meta["source"] == "test-input"
        assert "document_hash" in chunk_meta
        assert "chunk_index" in chunk_meta
        assert "total_chunks" in chunk_meta

    def test_process_text_small_chunks(self, small_chunk_processor):
        """With small chunk size, longer text should produce multiple chunks."""
        text = "Word " * 100  # ~500 chars
        result = small_chunk_processor.process_text(text)
        assert len(result) > 1

    def test_process_text_chunk_indices(self, small_chunk_processor):
        """Chunk indices should be sequential starting from 0."""
        text = "Word " * 100
        result = small_chunk_processor.process_text(text)
        indices = [c["metadata"]["chunk_index"] for c in result]
        assert indices == list(range(len(result)))
        assert all(c["metadata"]["total_chunks"] == len(result) for c in result)

    def test_process_file_for_indexing(self, processor):
        """process_file_for_indexing should read and chunk a text file."""
        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".txt", delete=False
        ) as f:
            # Content must exceed min_chunk_size (default 100 chars)
            f.write("This is test content for RAG document processing. " * 10)
            f.flush()
            tmp_path = f.name

        try:
            result = processor.process_file_for_indexing(tmp_path)
            assert isinstance(result, list)
            assert len(result) >= 1
            chunk = result[0]
            assert "content" in chunk
            assert "metadata" in chunk
            assert chunk["metadata"]["file_type"] == "txt"
            assert "file_name" in chunk["metadata"]
        finally:
            os.unlink(tmp_path)

    def test_process_file_not_found(self, processor):
        """Missing file should raise FileNotFoundError."""
        with pytest.raises(FileNotFoundError):
            processor.process_file_for_indexing("/nonexistent/file.txt")

    def test_process_files_for_indexing(self, processor):
        """Batch file processing should combine chunks from all files."""
        files = []
        try:
            for i in range(3):
                with tempfile.NamedTemporaryFile(
                    mode="w", suffix=".txt", delete=False
                ) as f:
                    # Content must exceed min_chunk_size (default 100 chars)
                    f.write(f"Document {i} content for testing batch processing. " * 10)
                    f.flush()
                    files.append(f.name)

            result = processor.process_files_for_indexing(files)
            assert isinstance(result, list)
            assert len(result) >= 3  # At least one chunk per file
        finally:
            for fp in files:
                os.unlink(fp)

    def test_process_files_skip_errors(self, processor):
        """With skip_errors=True, bad files should be skipped."""
        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".txt", delete=False
        ) as f:
            f.write("Valid content for testing skip errors behavior. " * 10)
            f.flush()
            valid_path = f.name

        try:
            result = processor.process_files_for_indexing(
                [valid_path, "/nonexistent/file.txt"],
                skip_errors=True,
            )
            # Should have chunks from the valid file only
            assert len(result) >= 1
        finally:
            os.unlink(valid_path)

    def test_process_files_no_skip_errors(self, processor):
        """With skip_errors=False, bad files should raise."""
        with pytest.raises((FileNotFoundError, ValueError)):
            processor.process_files_for_indexing(
                ["/nonexistent/file.txt"],
                skip_errors=False,
            )

    def test_process_directory_for_indexing(self, processor):
        """process_directory_for_indexing should process files in a dir."""
        with tempfile.TemporaryDirectory() as tmpdir:
            # Create files with enough content to exceed min_chunk_size
            for name in ["doc1.txt", "doc2.txt"]:
                (Path(tmpdir) / name).write_text(
                    f"Content of {name} for directory processing test. " * 10
                )

            result = processor.process_directory_for_indexing(tmpdir)
            assert isinstance(result, list)
            assert len(result) >= 2

    def test_process_directory_not_a_directory(self, processor):
        """Non-directory path should raise NotADirectoryError."""
        with tempfile.NamedTemporaryFile(suffix=".txt") as f:
            with pytest.raises(NotADirectoryError):
                processor.process_directory_for_indexing(f.name)


class TestTextChunker:
    """Tests for TextChunker through the RAG module import."""

    def test_fixed_size_chunking(self):
        """Fixed-size chunking should produce expected number of chunks."""
        config = ChunkConfig(
            strategy=ChunkStrategy.FIXED_SIZE,
            chunk_size=20,
            chunk_overlap=5,
            min_chunk_size=5,
        )
        chunker = TextChunker(config)
        text = "A" * 100
        doc = Document(content=text, metadata={})
        chunks = chunker.chunk(text, doc)
        assert len(chunks) > 1
        for chunk in chunks:
            assert isinstance(chunk, DocumentChunk)
            assert len(chunk.content) <= config.max_chunk_size

    def test_sentence_chunking(self):
        """Sentence chunking should split on sentence boundaries."""
        config = ChunkConfig(
            strategy=ChunkStrategy.SENTENCE,
            chunk_size=100,
            min_chunk_size=5,
        )
        chunker = TextChunker(config)
        text = "First sentence. Second sentence. Third sentence. Fourth one."
        doc = Document(content=text, metadata={})
        chunks = chunker.chunk(text, doc)
        assert len(chunks) >= 1
        for chunk in chunks:
            assert isinstance(chunk, DocumentChunk)


class TestDocument:
    """Tests for Document dataclass."""

    def test_auto_hash_generation(self):
        """Document should auto-generate hash if not provided."""
        doc = Document(content="Test content", metadata={})
        assert doc.hash is not None
        assert len(doc.hash) == 64  # SHA-256 hex digest

    def test_same_content_same_hash(self):
        """Documents with same content should have same hash."""
        doc1 = Document(content="Same content", metadata={})
        doc2 = Document(content="Same content", metadata={"key": "val"})
        assert doc1.hash == doc2.hash

    def test_different_content_different_hash(self):
        """Documents with different content should have different hashes."""
        doc1 = Document(content="Content A", metadata={})
        doc2 = Document(content="Content B", metadata={})
        assert doc1.hash != doc2.hash
