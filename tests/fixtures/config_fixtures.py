"""
Configuration Fixtures
Test configuration and environment setup
"""

from typing import Dict, Any
import os


def test_config() -> Dict[str, Any]:
    """Generate test configuration"""
    return {
        "backend_url": "http://localhost:8010",
        "ws_url": "ws://localhost:8010/ws",
        "api_timeout": 30,
        "max_retries": 3,
        "log_level": "DEBUG",
        "data_dir": "/tmp/windows_ai_test",
        "plugins_dir": "/tmp/windows_ai_test/plugins",
        "models_dir": "/tmp/windows_ai_test/models"
    }


def mock_env_vars() -> Dict[str, str]:
    """Generate mock environment variables"""
    return {
        "WINDOWS_AI_ENV": "test",
        "WINDOWS_AI_DEBUG": "true",
        "WINDOWS_AI_DATA_DIR": "/tmp/windows_ai_test",
        "WINDOWS_AI_LOG_LEVEL": "DEBUG",
        "OPENAI_API_KEY": "test-api-key-12345",
        "ANTHROPIC_API_KEY": "test-api-key-67890"
    }


def apply_test_env_vars(env_vars: Dict[str, str] = None):
    """Apply test environment variables"""
    vars_to_apply = env_vars or mock_env_vars()

    for key, value in vars_to_apply.items():
        os.environ[key] = value


def cleanup_test_env_vars(env_vars: Dict[str, str] = None):
    """Clean up test environment variables"""
    vars_to_cleanup = env_vars or mock_env_vars()

    for key in vars_to_cleanup.keys():
        os.environ.pop(key, None)
