"""
File System Testing Helpers
Utilities for creating and managing test files and directories
"""

import tempfile
import shutil
from pathlib import Path
from typing import Optional, List
from contextlib import contextmanager


@contextmanager
def create_temp_directory():
    """Context manager for temporary directory that auto-cleans up"""
    temp_dir = Path(tempfile.mkdtemp())
    try:
        yield temp_dir
    finally:
        if temp_dir.exists():
            shutil.rmtree(temp_dir)


def create_temp_file(
    content: str = "",
    suffix: str = ".txt",
    dir: Optional[Path] = None
) -> Path:
    """Create a temporary file with content"""
    fd, path = tempfile.mkstemp(suffix=suffix, dir=dir)

    if content:
        with open(path, 'w') as f:
            f.write(content)

    return Path(path)


def create_test_file_structure(base_dir: Path, structure: dict):
    """
    Create a file structure from a nested dictionary

    Example:
        structure = {
            "dir1": {
                "file1.txt": "content1",
                "file2.txt": "content2",
                "subdir": {
                    "file3.txt": "content3"
                }
            }
        }
    """
    for name, value in structure.items():
        path = base_dir / name

        if isinstance(value, dict):
            # It's a directory
            path.mkdir(parents=True, exist_ok=True)
            create_test_file_structure(path, value)
        else:
            # It's a file
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(str(value))


def cleanup_temp_files(paths: List[Path]):
    """Clean up temporary files and directories"""
    for path in paths:
        if path.exists():
            if path.is_dir():
                shutil.rmtree(path)
            else:
                path.unlink()


def assert_file_exists(path: Path, message: str = ""):
    """Assert that a file exists"""
    assert path.exists(), message or f"File does not exist: {path}"


def assert_file_contains(path: Path, content: str):
    """Assert that a file contains specific content"""
    assert path.exists(), f"File does not exist: {path}"
    actual_content = path.read_text()
    assert content in actual_content, \
        f"Expected content not found in {path}. Looking for: {content}"


def assert_directory_structure(base_dir: Path, expected_structure: dict):
    """Assert that a directory has expected structure"""
    for name, value in expected_structure.items():
        path = base_dir / name

        if isinstance(value, dict):
            assert path.is_dir(), f"Expected directory: {path}"
            assert_directory_structure(path, value)
        else:
            assert path.is_file(), f"Expected file: {path}"
            if value is not None:
                assert path.read_text() == str(value)
