"""
Tests for Windows File Organizer Plugin
"""

import pytest
from pathlib import Path

from windows_ai.plugins.builtin.windows_file_organizer import WindowsFileOrganizerPlugin


class TestWindowsFileOrganizerPlugin:
    """Test suite for File Organizer Plugin"""

    @pytest.fixture
    def plugin(self):
        """Create plugin instance"""
        return WindowsFileOrganizerPlugin()

    @pytest.fixture
    def test_directory(self, tmp_path):
        """Create test directory with files"""
        test_dir = tmp_path / "organize_test"
        test_dir.mkdir()

        # Create test files
        (test_dir / "document.pdf").write_text("PDF content")
        (test_dir / "image.jpg").write_bytes(b"JPEG data")
        (test_dir / "script.py").write_text("print('hello')")
        (test_dir / "data.csv").write_text("a,b,c\n1,2,3")
        (test_dir / "archive.zip").write_bytes(b"ZIP data")

        return test_dir

    @pytest.mark.asyncio
    async def test_initialization(self, plugin):
        """Test plugin initialization"""
        result = await plugin.initialize()
        assert result is True
        assert plugin.metadata.id == "windows_file_organizer"

    @pytest.mark.asyncio
    async def test_organize_by_type_dry_run(self, plugin, test_directory):
        """Test organization by type (dry run)"""
        result = await plugin.execute(
            input_data=str(test_directory),
            strategy="type",
            dry_run=True
        )

        assert result["success"] is True
        assert "result" in result
        assert "categories" in result["result"]
        assert result["metadata"]["dry_run"] is True

        # Check that files weren't actually moved
        assert (test_directory / "document.pdf").exists()
        assert (test_directory / "image.jpg").exists()

    @pytest.mark.asyncio
    async def test_organize_by_type_execute(self, plugin, test_directory):
        """Test actual organization by type"""
        result = await plugin.execute(
            input_data=str(test_directory),
            strategy="type",
            dry_run=False,
            create_categories=True
        )

        assert result["success"] is True
        assert result["result"]["files_moved"] > 0

        # Check that category folders were created
        documents_dir = test_directory / "Documents"
        images_dir = test_directory / "Images"

        # At least one category should exist
        assert documents_dir.exists() or images_dir.exists()

    @pytest.mark.asyncio
    async def test_organize_by_date(self, plugin, test_directory):
        """Test organization by date"""
        result = await plugin.execute(
            input_data=str(test_directory),
            strategy="date",
            dry_run=True
        )

        assert result["success"] is True
        assert "categories" in result["result"]

    @pytest.mark.asyncio
    async def test_organize_by_size(self, plugin, test_directory):
        """Test organization by size"""
        result = await plugin.execute(
            input_data=str(test_directory),
            strategy="size",
            dry_run=True
        )

        assert result["success"] is True
        assert "categories" in result["result"]

    @pytest.mark.asyncio
    async def test_duplicate_detection(self, plugin, test_directory):
        """Test duplicate file detection"""
        # Create duplicate file
        original = test_directory / "file1.txt"
        duplicate = test_directory / "file2.txt"

        content = "Same content"
        original.write_text(content)
        duplicate.write_text(content)

        result = await plugin.execute(
            input_data=str(test_directory),
            strategy="type",
            dry_run=True,
            detect_duplicates=True
        )

        assert result["success"] is True
        assert "duplicates" in result["result"]
        # Should detect at least one duplicate set
        assert len(result["result"]["duplicates"]) > 0

    @pytest.mark.asyncio
    async def test_invalid_directory(self, plugin):
        """Test with invalid directory"""
        result = await plugin.execute(
            input_data="/nonexistent/path",
            strategy="type"
        )

        assert result["success"] is False
        assert "error" in result

    @pytest.mark.asyncio
    async def test_exclusions(self, plugin, test_directory):
        """Test file exclusions"""
        # Create files to exclude
        (test_directory / "temp.tmp").write_text("temp")
        (test_directory / "log.log").write_text("log")

        result = await plugin.execute(
            input_data=str(test_directory),
            strategy="type",
            dry_run=True,
            exclude_extensions=[".tmp", ".log"]
        )

        assert result["success"] is True

        # Check that excluded files weren't included in organization
        all_files = []
        for category_files in result["result"]["categories"].values():
            all_files.extend([f["from"] for f in category_files["files"]])

        assert not any("temp.tmp" in f for f in all_files)
        assert not any("log.log" in f for f in all_files)

    @pytest.mark.asyncio
    async def test_min_file_size(self, plugin, test_directory):
        """Test minimum file size filter"""
        # Create small and large files
        (test_directory / "small.txt").write_text("x")
        (test_directory / "large.txt").write_text("x" * 10000)

        result = await plugin.execute(
            input_data=str(test_directory),
            strategy="type",
            dry_run=True,
            min_file_size=5000  # 5KB
        )

        assert result["success"] is True

        # Small file should be excluded
        all_files = []
        for category_files in result["result"]["categories"].values():
            all_files.extend([f["from"] for f in category_files["files"]])

        assert not any("small.txt" in f for f in all_files)
        assert any("large.txt" in f for f in all_files)

    def test_get_schema(self, plugin):
        """Test schema generation"""
        schema = plugin.get_schema()

        assert "properties" in schema
        assert "directory" in schema["properties"]
        assert "strategy" in schema["properties"]
        assert "type" in schema["required"]
