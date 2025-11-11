"""
Tests for document processing
"""
import pytest
from pathlib import Path
import tempfile

from windows_ai.document_processor import (
    DocumentProcessor,
    ChunkConfig,
    ChunkStrategy,
    FileReader,
    FileType,
    Document,
    TextChunker
)


class TestFileReader:
    """Test file reading functionality"""

    def test_detect_file_type(self):
        """Test file type detection"""
        assert FileReader.detect_file_type(Path("test.txt")) == FileType.TXT
        assert FileReader.detect_file_type(Path("test.pdf")) == FileType.PDF
        assert FileReader.detect_file_type(Path("test.docx")) == FileType.DOCX
        assert FileReader.detect_file_type(Path("test.md")) == FileType.MD
        assert FileReader.detect_file_type(Path("test.json")) == FileType.JSON
        assert FileReader.detect_file_type(Path("test.csv")) == FileType.CSV
        assert FileReader.detect_file_type(Path("test.html")) == FileType.HTML
        assert FileReader.detect_file_type(Path("test.unknown")) == FileType.UNKNOWN

    def test_read_txt_file(self):
        """Test reading text files"""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as f:
            f.write("This is a test document.\nWith multiple lines.")
            temp_path = Path(f.name)

        try:
            content = FileReader.read_txt(temp_path)
            assert "This is a test document" in content
            assert "With multiple lines" in content
        finally:
            temp_path.unlink()

    def test_read_json_file(self):
        """Test reading JSON files"""
        import json

        data = {"key1": "value1", "key2": "value2"}

        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            json.dump(data, f)
            temp_path = Path(f.name)

        try:
            content = FileReader.read_json(temp_path)
            assert "key1" in content
            assert "value1" in content
        finally:
            temp_path.unlink()

    def test_read_csv_file(self):
        """Test reading CSV files"""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as f:
            f.write("Name,Age,City\n")
            f.write("Alice,30,New York\n")
            f.write("Bob,25,Los Angeles\n")
            temp_path = Path(f.name)

        try:
            content = FileReader.read_csv(temp_path)
            assert "Name" in content
            assert "Alice" in content
            assert "New York" in content
        finally:
            temp_path.unlink()


class TestTextChunker:
    """Test text chunking strategies"""

    def create_test_document(self, text):
        """Create test document"""
        return Document(
            content=text,
            metadata={"test": True}
        )

    def test_fixed_size_chunking(self):
        """Test fixed size chunking"""
        text = "This is a test document. " * 100  # Long text
        config = ChunkConfig(
            strategy=ChunkStrategy.FIXED_SIZE,
            chunk_size=100,
            chunk_overlap=10
        )

        chunker = TextChunker(config)
        document = self.create_test_document(text)
        chunks = chunker.chunk(text, document)

        assert len(chunks) > 0
        for chunk in chunks:
            assert len(chunk.content) <= config.max_chunk_size
            assert chunk.document_hash == document.hash

    def test_semantic_chunking(self):
        """Test semantic chunking"""
        text = """
        This is the first paragraph. It has multiple sentences.

        This is the second paragraph. It also has content.

        This is the third paragraph.
        """

        config = ChunkConfig(
            strategy=ChunkStrategy.SEMANTIC,
            max_chunk_size=500
        )

        chunker = TextChunker(config)
        document = self.create_test_document(text)
        chunks = chunker.chunk(text, document)

        assert len(chunks) > 0
        # Check that chunks preserve paragraph structure
        for chunk in chunks:
            assert chunk.content.strip()

    def test_sentence_chunking(self):
        """Test sentence-based chunking"""
        text = "First sentence. Second sentence. Third sentence. Fourth sentence."

        config = ChunkConfig(
            strategy=ChunkStrategy.SENTENCE,
            chunk_size=50
        )

        chunker = TextChunker(config)
        document = self.create_test_document(text)
        chunks = chunker.chunk(text, document)

        assert len(chunks) > 0

    def test_paragraph_chunking(self):
        """Test paragraph chunking"""
        text = """Paragraph 1 here.

Paragraph 2 here.

Paragraph 3 here."""

        config = ChunkConfig(
            strategy=ChunkStrategy.PARAGRAPH,
            min_chunk_size=5
        )

        chunker = TextChunker(config)
        document = self.create_test_document(text)
        chunks = chunker.chunk(text, document)

        assert len(chunks) > 0

    def test_sliding_window_chunking(self):
        """Test sliding window chunking"""
        text = "word " * 200  # Long repetitive text

        config = ChunkConfig(
            strategy=ChunkStrategy.SLIDING_WINDOW,
            chunk_size=100,
            chunk_overlap=20
        )

        chunker = TextChunker(config)
        document = self.create_test_document(text)
        chunks = chunker.chunk(text, document)

        assert len(chunks) > 1

        # Check overlap
        if len(chunks) > 1:
            first_end = chunks[0].content[-20:]
            second_start = chunks[1].content[:20]
            # There should be some overlap
            assert len(first_end) > 0


class TestDocumentProcessor:
    """Test document processor"""

    def test_processor_initialization(self):
        """Test processor initialization"""
        config = ChunkConfig(chunk_size=256)
        processor = DocumentProcessor(config)

        assert processor.chunk_config.chunk_size == 256

    def test_process_txt_file(self):
        """Test processing text file"""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as f:
            f.write("This is a test document for processing. " * 50)
            temp_path = Path(f.name)

        try:
            processor = DocumentProcessor()
            document, chunks = processor.process_file(str(temp_path))

            assert document.file_type == FileType.TXT
            assert document.content
            assert len(chunks) > 0
            assert all(chunk.content for chunk in chunks)

        finally:
            temp_path.unlink()

    def test_metadata_extraction(self):
        """Test metadata extraction"""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as f:
            f.write("Test content")
            temp_path = Path(f.name)

        try:
            processor = DocumentProcessor()
            document, _ = processor.process_file(str(temp_path))

            metadata = document.metadata
            assert 'file_name' in metadata
            assert 'file_size' in metadata
            assert 'content_length' in metadata
            assert 'word_count' in metadata
            assert 'created_at' in metadata

        finally:
            temp_path.unlink()

    def test_directory_processing(self):
        """Test processing directory"""
        with tempfile.TemporaryDirectory() as tmpdir:
            tmppath = Path(tmpdir)

            # Create test files
            (tmppath / "file1.txt").write_text("Document 1 content")
            (tmppath / "file2.txt").write_text("Document 2 content")

            processor = DocumentProcessor()
            results = processor.process_directory(
                str(tmppath),
                recursive=False,
                file_patterns=["*.txt"]
            )

            assert len(results) == 2

            for document, chunks in results:
                assert document.content
                assert len(chunks) > 0


class TestChunkConfig:
    """Test chunk configuration"""

    def test_default_config(self):
        """Test default configuration"""
        config = ChunkConfig()

        assert config.strategy == ChunkStrategy.FIXED_SIZE
        assert config.chunk_size == 512
        assert config.chunk_overlap == 50

    def test_custom_config(self):
        """Test custom configuration"""
        config = ChunkConfig(
            strategy=ChunkStrategy.SEMANTIC,
            chunk_size=1024,
            chunk_overlap=100,
            min_chunk_size=50,
            max_chunk_size=3000
        )

        assert config.strategy == ChunkStrategy.SEMANTIC
        assert config.chunk_size == 1024
        assert config.chunk_overlap == 100


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
