"""
Mocking Helpers
Utilities for creating mock objects and responses
"""

from unittest.mock import AsyncMock, Mock, MagicMock
from typing import Any, Dict, Optional
import httpx


def mock_httpx_client(
    status_code: int = 200,
    json_data: Optional[Dict] = None,
    text_data: Optional[str] = None
) -> AsyncMock:
    """
    Create a mock httpx.AsyncClient with configurable response

    Usage:
        mock_client = mock_httpx_client(200, {"key": "value"})
        async with mock_client as client:
            response = await client.get("http://test.com")
            assert response.status_code == 200
    """
    mock_response = AsyncMock()
    mock_response.status_code = status_code
    mock_response.json.return_value = json_data or {}
    mock_response.text = text_data or ""
    mock_response.headers = {}

    mock_client = AsyncMock()
    mock_client.get.return_value = mock_response
    mock_client.post.return_value = mock_response
    mock_client.put.return_value = mock_response
    mock_client.delete.return_value = mock_response
    mock_client.patch.return_value = mock_response

    # Support async context manager
    mock_client.__aenter__.return_value = mock_client
    mock_client.__aexit__.return_value = AsyncMock()

    return mock_client


def mock_async_response(
    status_code: int = 200,
    json_data: Optional[Dict] = None,
    text: Optional[str] = None,
    headers: Optional[Dict] = None
) -> AsyncMock:
    """Create a mock async HTTP response"""
    response = AsyncMock(spec=httpx.Response)
    response.status_code = status_code
    response.json.return_value = json_data or {}
    response.text = text or ""
    response.headers = headers or {}
    response.content = (text or "").encode()

    return response


def mock_process(
    pid: int = 1234,
    name: str = "test_process",
    status: str = "running",
    cpu_percent: float = 10.0,
    memory_mb: float = 100.0
) -> Mock:
    """Create a mock process object for psutil"""
    process = Mock()
    process.pid = pid
    process.name.return_value = name
    process.status.return_value = status
    process.cpu_percent.return_value = cpu_percent
    process.memory_info.return_value = Mock(rss=int(memory_mb * 1024 * 1024))
    process.num_threads.return_value = 4
    process.username.return_value = "test_user"
    process.is_running.return_value = True

    return process


def mock_file_system():
    """Create a mock file system for testing file operations"""
    mock_fs = MagicMock()
    mock_fs.files = {}

    def mock_exists(path):
        return str(path) in mock_fs.files

    def mock_read_text(path):
        if str(path) in mock_fs.files:
            return mock_fs.files[str(path)]
        raise FileNotFoundError(path)

    def mock_write_text(path, content):
        mock_fs.files[str(path)] = content

    mock_fs.exists = mock_exists
    mock_fs.read_text = mock_read_text
    mock_fs.write_text = mock_write_text

    return mock_fs


class AsyncContextManagerMock:
    """Helper for mocking async context managers"""

    def __init__(self, return_value=None):
        self.return_value = return_value
        self.aenter_called = False
        self.aexit_called = False

    async def __aenter__(self):
        self.aenter_called = True
        return self.return_value or self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        self.aexit_called = True
        return False
