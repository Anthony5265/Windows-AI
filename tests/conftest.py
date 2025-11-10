"""
Pytest configuration and shared fixtures for Windows-AI tests.

This module provides common fixtures, test utilities, and configuration
used across all test suites (unit, integration, E2E).
"""

import asyncio
import os
import sys
from pathlib import Path
from typing import AsyncGenerator, Generator
from unittest.mock import MagicMock, AsyncMock

import pytest
from httpx import AsyncClient

# Add project root to Python path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))


# ============================================================================
# Session-scoped fixtures (run once per test session)
# ============================================================================

@pytest.fixture(scope="session")
def event_loop():
    """
    Create an instance of the default event loop for the test session.
    Required for async tests.
    """
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture(scope="session")
def test_data_dir() -> Path:
    """Return path to test data directory."""
    data_dir = Path(__file__).parent / "data"
    data_dir.mkdir(exist_ok=True)
    return data_dir


@pytest.fixture(scope="session")
def temp_dir(tmp_path_factory) -> Path:
    """Return a temporary directory for test files."""
    return tmp_path_factory.mktemp("windows_ai_tests")


# ============================================================================
# Function-scoped fixtures (run for each test)
# ============================================================================

@pytest.fixture
def mock_env_vars(monkeypatch):
    """
    Provide mock environment variables for testing.
    Prevents tests from using real API keys or credentials.
    """
    env_vars = {
        "OPENAI_API_KEY": "test-openai-key-123",
        "ANTHROPIC_API_KEY": "test-anthropic-key-456",
        "GOOGLE_API_KEY": "test-google-key-789",
        "BACKEND_URL": "http://localhost:8000",
        "OLLAMA_HOST": "http://localhost:11434",
        "TESTING": "true",
    }
    for key, value in env_vars.items():
        monkeypatch.setenv(key, value)
    return env_vars


@pytest.fixture
async def async_client() -> AsyncGenerator[AsyncClient, None]:
    """
    Provide an async HTTP client for integration tests.

    Usage:
        async def test_endpoint(async_client):
            response = await async_client.get("/api/health")
            assert response.status_code == 200
    """
    from windows_ai.main import app

    async with AsyncClient(app=app, base_url="http://test") as client:
        yield client


@pytest.fixture
def mock_ollama_client():
    """Mock Ollama client for testing model operations."""
    mock = MagicMock()
    mock.list = AsyncMock(return_value={
        "models": [
            {"name": "llama2:7b", "size": 3800000000},
            {"name": "codellama:7b", "size": 3800000000},
        ]
    })
    mock.pull = AsyncMock(return_value={"status": "success"})
    mock.delete = AsyncMock(return_value={"status": "success"})
    return mock


@pytest.fixture
def sample_conversation():
    """Provide sample conversation data for testing."""
    return {
        "id": "conv-123",
        "title": "Test Conversation",
        "messages": [
            {
                "role": "user",
                "content": "Hello, how are you?",
                "timestamp": "2025-11-10T10:00:00Z"
            },
            {
                "role": "assistant",
                "content": "I'm doing well, thank you! How can I help you today?",
                "timestamp": "2025-11-10T10:00:05Z"
            }
        ],
        "created_at": "2025-11-10T10:00:00Z",
        "updated_at": "2025-11-10T10:00:05Z"
    }


@pytest.fixture
def sample_model():
    """Provide sample AI model data for testing."""
    return {
        "id": "llama2:7b",
        "name": "Llama 2 7B",
        "provider": "Ollama",
        "category": "general",
        "size": "3.8 GB",
        "description": "General purpose language model",
        "recommended": True,
        "installed": False
    }


@pytest.fixture
def sample_plugin():
    """Provide sample plugin data for testing."""
    return {
        "id": "test_plugin",
        "name": "Test Plugin",
        "description": "A test plugin for unit tests",
        "version": "1.0.0",
        "enabled": False,
        "parameters": {
            "param1": {
                "type": "string",
                "required": True,
                "description": "Test parameter"
            }
        }
    }


@pytest.fixture
def sample_watcher():
    """Provide sample folder watcher configuration."""
    return {
        "id": "watcher-123",
        "name": "Test Watcher",
        "path": "/tmp/test-folder",
        "patterns": ["*.txt", "*.pdf"],
        "events": ["created", "modified"],
        "action": "organize",
        "enabled": True
    }


@pytest.fixture
def sample_task():
    """Provide sample scheduled task configuration."""
    return {
        "id": "task-456",
        "name": "Test Task",
        "description": "A test scheduled task",
        "schedule_type": "cron",
        "schedule": "0 9 * * *",  # Daily at 9 AM
        "action": "cleanup",
        "prompt": "Clean up temporary files",
        "enabled": True
    }


# ============================================================================
# Test markers and utilities
# ============================================================================

def pytest_configure(config):
    """Configure custom markers."""
    config.addinivalue_line(
        "markers", "unit: mark test as a unit test"
    )
    config.addinivalue_line(
        "markers", "integration: mark test as an integration test"
    )
    config.addinivalue_line(
        "markers", "e2e: mark test as an end-to-end test"
    )
    config.addinivalue_line(
        "markers", "slow: mark test as slow (> 1 second)"
    )
    config.addinivalue_line(
        "markers", "benchmark: mark test as a performance benchmark"
    )


@pytest.fixture(autouse=True)
def reset_environment():
    """
    Reset environment between tests.

    This fixture runs automatically before each test to ensure
    a clean state.
    """
    yield
    # Cleanup after test if needed


# ============================================================================
# Helper functions
# ============================================================================

def assert_valid_response(response, expected_status=200):
    """
    Helper to assert HTTP response is valid.

    Args:
        response: HTTP response object
        expected_status: Expected HTTP status code (default: 200)
    """
    assert response.status_code == expected_status, \
        f"Expected status {expected_status}, got {response.status_code}: {response.text}"

    if response.status_code == 200:
        assert response.json() is not None, "Response should contain JSON data"


def assert_valid_model(model_data):
    """Assert that model data has required fields."""
    required_fields = ["id", "name", "provider", "size"]
    for field in required_fields:
        assert field in model_data, f"Model missing required field: {field}"


def assert_valid_conversation(conversation_data):
    """Assert that conversation data has required fields."""
    required_fields = ["id", "title", "messages", "created_at"]
    for field in required_fields:
        assert field in conversation_data, f"Conversation missing required field: {field}"


def create_mock_file(tmp_path, filename, content="test content"):
    """
    Create a mock file for testing.

    Args:
        tmp_path: Temporary directory path
        filename: Name of file to create
        content: File content (default: "test content")

    Returns:
        Path to created file
    """
    file_path = tmp_path / filename
    file_path.write_text(content)
    return file_path
