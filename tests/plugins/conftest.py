"""
Pytest configuration and fixtures for plugin tests
"""

import pytest
import asyncio
from pathlib import Path
from typing import Dict, Any
from unittest.mock import Mock, AsyncMock

from windows_ai.plugins.base import Plugin, PluginMetadata, PluginType
from windows_ai.plugins.registry import PluginRegistry


@pytest.fixture
def event_loop():
    """Create event loop for async tests"""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture
def plugin_metadata():
    """Sample plugin metadata"""
    return PluginMetadata(
        id="test_plugin",
        name="Test Plugin",
        description="A test plugin",
        version="1.0.0",
        author="Test Author",
        plugin_type=PluginType.ACTION,
        enabled=True,
        tags=["test", "sample"]
    )


@pytest.fixture
def plugins_dir(tmp_path):
    """Create temporary plugins directory"""
    plugins_path = tmp_path / "plugins" / "builtin"
    plugins_path.mkdir(parents=True, exist_ok=True)
    return plugins_path


@pytest.fixture
async def plugin_registry(plugins_dir):
    """Create plugin registry for testing"""
    registry = PluginRegistry(plugins_dir)
    yield registry
    await registry.shutdown_plugins()


@pytest.fixture
def mock_httpx_client():
    """Mock httpx.AsyncClient for testing integrations"""
    mock_client = AsyncMock()
    mock_response = AsyncMock()
    mock_response.status_code = 200
    mock_response.json.return_value = {"status": "success"}
    mock_client.post.return_value = mock_response
    mock_client.get.return_value = mock_response
    return mock_client


@pytest.fixture
def sample_files(tmp_path):
    """Create sample files for testing file operations"""
    files_dir = tmp_path / "test_files"
    files_dir.mkdir(exist_ok=True)

    # Create various file types
    (files_dir / "document.txt").write_text("Sample text file")
    (files_dir / "image.png").write_bytes(b"PNG data")
    (files_dir / "script.py").write_text("print('hello')")
    (files_dir / "data.json").write_text('{"key": "value"}')

    return files_dir


@pytest.fixture
def mock_ollama_server():
    """Mock Ollama server responses"""
    class MockOllamaServer:
        def __init__(self):
            self.base_url = "http://localhost:11434"

        def get_models_response(self):
            return {
                "models": [
                    {
                        "name": "llama2",
                        "size": 3826793677,
                        "modified_at": "2024-01-01T00:00:00Z"
                    }
                ]
            }

        def get_chat_response(self, message: str):
            return {
                "message": {
                    "role": "assistant",
                    "content": f"Response to: {message}"
                }
            }

        def get_generate_response(self, prompt: str):
            return {
                "response": f"Generated: {prompt}"
            }

    return MockOllamaServer()
