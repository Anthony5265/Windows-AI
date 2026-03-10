"""
Pytest fixtures for core module testing

Provides reusable test fixtures for Windows AI core components
"""

import pytest
from unittest.mock import Mock, AsyncMock
from pathlib import Path
import tempfile
import shutil

from windows_ai.plugins.base import Plugin, PluginMetadata, PluginType


@pytest.fixture
def temp_dir():
    """Create a temporary directory for testing"""
    temp_path = Path(tempfile.mkdtemp())
    yield temp_path
    # Cleanup
    if temp_path.exists():
        shutil.rmtree(temp_path, ignore_errors=True)


@pytest.fixture
def mock_plugin():
    """Create a mock plugin for testing"""
    metadata = PluginMetadata(
        id="test_plugin",
        name="Test Plugin",
        description="A test plugin for unit testing",
        version="1.0.0",
        author="Test Suite",
        plugin_type=PluginType.INTEGRATION,
        tags=["test", "mock", "unit-test"]
    )

    plugin = Mock(spec=Plugin)
    plugin.metadata = metadata
    plugin.initialize = AsyncMock(return_value=True)
    plugin.execute = AsyncMock(return_value={"status": "success", "data": "test result"})
    plugin.shutdown = AsyncMock(return_value=True)
    plugin.get_supported_models = Mock(return_value=[
        {"id": "test_model_1", "name": "Test Model 1"},
        {"id": "test_model_2", "name": "Test Model 2"}
    ])

    return plugin


@pytest.fixture
def mock_ai_manager():
    """Create a mock AI manager for testing"""
    manager = Mock()
    manager.initialize = AsyncMock(return_value=True)
    manager.chat = AsyncMock(return_value="AI response")
    manager.health_check = AsyncMock(return_value={"status": "healthy"})
    manager.list_capabilities = Mock(return_value=["chat", "completion", "embedding"])
    manager.cleanup = AsyncMock(return_value=True)
    return manager


@pytest.fixture
def mock_config():
    """Create a mock configuration object"""
    config = Mock()
    config.environment = "test"
    config.version = "1.0.0-test"
    config.llm = Mock()
    config.llm.api_key = "test_key"
    config.llm.model = "gpt-4"
    config.llm.temperature = 0.7
    config.database = Mock()
    config.database.url = "sqlite:///:memory:"
    config.database.password = "test_password"
    config.set_nested = Mock()
    config.model_dump = Mock(return_value={
        "environment": "test",
        "version": "1.0.0-test"
    })
    return config


@pytest.fixture
def mock_credentials():
    """Provide mock credentials for testing"""
    return {
        "openai": {
            "api_key": "sk-test-openai-key-123",
            "org_id": "org-test-123"
        },
        "anthropic": {
            "api_key": "ant-test-key-456"
        },
        "google": {
            "api_key": "google-test-key-789"
        }
    }


@pytest.fixture
def sample_api_response():
    """Provide sample API response data"""
    return {
        "id": "chatcmpl-test123",
        "object": "chat.completion",
        "created": 1234567890,
        "model": "gpt-4",
        "choices": [
            {
                "index": 0,
                "message": {
                    "role": "assistant",
                    "content": "This is a test response"
                },
                "finish_reason": "stop"
            }
        ],
        "usage": {
            "prompt_tokens": 10,
            "completion_tokens": 20,
            "total_tokens": 30
        }
    }


@pytest.fixture
def sample_image_data():
    """Provide sample image binary data"""
    # 1x1 red pixel PNG
    return b'\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x01\x00\x00\x00\x01\x08\x02\x00\x00\x00\x90wS\xde\x00\x00\x00\x0cIDATx\x9cc\xf8\xcf\xc0\x00\x00\x00\x03\x00\x01\x00\x00\x00\x00IEND\xaeB`\x82'


@pytest.fixture
def sample_audio_data():
    """Provide sample audio binary data"""
    # Minimal WAV file header
    return b'RIFF$\x00\x00\x00WAVEfmt \x10\x00\x00\x00\x01\x00\x01\x00D\xac\x00\x00\x88X\x01\x00\x02\x00\x10\x00data\x00\x00\x00\x00'


@pytest.fixture
def mock_database():
    """Create a mock database connection"""
    db = Mock()
    db.execute = AsyncMock(return_value=Mock(fetchall=Mock(return_value=[])))
    db.commit = AsyncMock()
    db.rollback = AsyncMock()
    db.close = AsyncMock()
    return db


@pytest.fixture
def mock_file_system(temp_dir):
    """Create a mock file system structure for testing"""
    # Create test directories
    (temp_dir / "plugins").mkdir()
    (temp_dir / "models").mkdir()
    (temp_dir / "logs").mkdir()
    (temp_dir / "config").mkdir()

    # Create test files
    (temp_dir / "config" / "config.json").write_text('{"test": true}')
    (temp_dir / "plugins" / "test_plugin.py").write_text('# Test plugin')

    return temp_dir


@pytest.fixture
def mock_logger():
    """Create a mock logger for testing"""
    logger = Mock()
    logger.debug = Mock()
    logger.info = Mock()
    logger.warning = Mock()
    logger.error = Mock()
    logger.critical = Mock()
    logger.exception = Mock()
    return logger


@pytest.fixture
def mock_http_client():
    """Create a mock HTTP client"""
    client = Mock()
    client.get = AsyncMock(return_value=Mock(
        status_code=200,
        json=Mock(return_value={"status": "ok"}),
        text="OK"
    ))
    client.post = AsyncMock(return_value=Mock(
        status_code=200,
        json=Mock(return_value={"status": "success"}),
        text="Success"
    ))
    client.put = AsyncMock(return_value=Mock(
        status_code=200,
        json=Mock(return_value={"status": "updated"}),
        text="Updated"
    ))
    client.delete = AsyncMock(return_value=Mock(
        status_code=204,
        text=""
    ))
    return client


@pytest.fixture
def mock_event_loop():
    """Create a mock event loop"""
    import asyncio
    loop = asyncio.new_event_loop()
    yield loop
    loop.close()


@pytest.fixture
async def async_cleanup():
    """Fixture for async cleanup tasks"""
    cleanup_tasks = []

    def register_cleanup(coro):
        cleanup_tasks.append(coro)

    yield register_cleanup

    # Run all cleanup tasks
    for task in cleanup_tasks:
        try:
            await task()
        except Exception:
            pass


@pytest.fixture
def mock_environment_variables():
    """Provide mock environment variables"""
    return {
        "WINDOWS_AI_ENV": "test",
        "OPENAI_API_KEY": "sk-test123",
        "ANTHROPIC_API_KEY": "ant-test456",
        "LOG_LEVEL": "DEBUG"
    }


@pytest.fixture
def sample_plugin_code():
    """Provide sample plugin code for dynamic loading tests"""
    return '''
from windows_ai.plugins.base import Plugin, PluginMetadata, PluginType

metadata = PluginMetadata(
    id="dynamic_test_plugin",
    name="Dynamic Test Plugin",
    description="A dynamically loaded test plugin",
    version="1.0.0",
    author="Test Suite",
    plugin_type=PluginType.UTILITY,
    tags=["dynamic", "test"]
)

class DynamicTestPlugin(Plugin):
    def __init__(self):
        super().__init__(metadata)

    async def initialize(self):
        return True

    async def execute(self, action, params):
        return {"status": "success", "action": action, "params": params}

    async def shutdown(self):
        return True

plugin = DynamicTestPlugin()
'''


@pytest.fixture
def performance_timer():
    """Fixture for measuring performance in tests"""
    import time

    class PerformanceTimer:
        def __init__(self):
            self.start_time = None
            self.end_time = None

        def start(self):
            self.start_time = time.perf_counter()

        def stop(self):
            self.end_time = time.perf_counter()

        @property
        def elapsed(self):
            if self.start_time is None or self.end_time is None:
                return None
            return self.end_time - self.start_time

        def assert_faster_than(self, seconds):
            assert self.elapsed < seconds, f"Operation took {self.elapsed}s, expected < {seconds}s"

    return PerformanceTimer()


@pytest.fixture
def mock_subprocess():
    """Create a mock subprocess for testing CLI commands"""
    subprocess = Mock()
    subprocess.run = Mock(return_value=Mock(
        returncode=0,
        stdout="Command output",
        stderr=""
    ))
    subprocess.Popen = Mock(return_value=Mock(
        communicate=Mock(return_value=("Output", "")),
        returncode=0,
        pid=12345
    ))
    return subprocess
