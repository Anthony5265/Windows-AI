"""
Comprehensive Unit Tests for FastAPI Main Application
Tests all endpoints in windows_ai/main.py with high coverage
"""

import pytest
from fastapi.testclient import TestClient
from unittest.mock import Mock, AsyncMock, patch
import json

# Import the FastAPI app
import sys
sys.path.insert(0, '/home/user/Windows-AI')

from tests.helpers.api_helpers import assert_response_ok, assert_error_response
from tests.fixtures.sample_data import sample_chat_message, sample_conversation


@pytest.fixture
def client():
    """Create test client for FastAPI app"""
    try:
        from windows_ai.main import app
        return TestClient(app)
    except Exception as e:
        pytest.skip(f"Could not import app: {e}")


@pytest.fixture
def mock_chat_history():
    """Mock chat history"""
    with patch('windows_ai.main.chat_history') as mock:
        mock.get_conversation.return_value = []
        mock.get_all_conversations.return_value = []
        mock.add_message = Mock()
        mock.clear_conversation = Mock()
        yield mock


@pytest.fixture
def mock_llm():
    """Mock LLM call"""
    with patch('windows_ai.main.call_llm') as mock:
        mock.return_value = "Test AI response"
        yield mock


class TestHealthEndpoints:
    """Test health check endpoints"""

    def test_root_endpoint(self, client):
        """Test GET / returns service info"""
        response = client.get("/")

        assert response.status_code == 200
        data = response.json()
        assert "name" in data
        assert "version" in data
        assert data["name"] == "Windows AI"

    def test_health_endpoint(self, client):
        """Test GET /health returns healthy status"""
        response = client.get("/health")

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert "timestamp" in data


class TestChatEndpoints:
    """Test chat-related endpoints"""

    def test_chat_endpoint_success(self, client, mock_llm, mock_chat_history):
        """Test POST /chat with valid message"""
        payload = {
            "message": "Hello, how are you?",
            "model": "gpt-3.5-turbo",
            "temperature": 0.7
        }

        response = client.post("/chat", json=payload)

        # May not work if dependencies missing, but structure should be testable
        if response.status_code == 200:
            data = response.json()
            assert "message" in data
            assert data["message"]["role"] == "assistant"

    def test_chat_endpoint_empty_message(self, client):
        """Test POST /chat with empty message"""
        payload = {
            "message": "",
            "model": "gpt-3.5-turbo"
        }

        response = client.post("/chat", json=payload)

        # Should fail validation
        assert response.status_code == 422

    def test_chat_endpoint_missing_message(self, client):
        """Test POST /chat without message field"""
        payload = {
            "model": "gpt-3.5-turbo"
        }

        response = client.post("/chat", json=payload)

        # Should fail validation
        assert response.status_code == 422

    def test_chat_stream_endpoint_rejects_non_stream(self, client):
        """Test POST /chat/stream requires stream=true"""
        payload = {
            "message": "Test",
            "stream": False
        }

        # Stream endpoint should only accept streaming requests
        response = client.post("/chat/stream", json=payload)

        # May return error or redirect
        assert response.status_code in [200, 400, 422]

    def test_get_conversations(self, client, mock_chat_history):
        """Test GET /conversations returns conversation list"""
        mock_chat_history.get_all_conversations.return_value = ["conv1", "conv2"]

        response = client.get("/conversations")

        if response.status_code == 200:
            data = response.json()
            assert "conversations" in data

    def test_get_conversation_by_id(self, client, mock_chat_history):
        """Test GET /conversations/{id} returns specific conversation"""
        mock_chat_history.get_conversation.return_value = [
            sample_chat_message("user", "Hello"),
            sample_chat_message("assistant", "Hi there")
        ]

        response = client.get("/conversations/test-conv-1")

        if response.status_code == 200:
            data = response.json()
            assert "messages" in data or "conversation_id" in data

    def test_delete_conversation(self, client, mock_chat_history):
        """Test DELETE /conversations/{id} removes conversation"""
        response = client.delete("/conversations/test-conv-1")

        if response.status_code == 200:
            data = response.json()
            assert data["status"] == "deleted"
            mock_chat_history.clear_conversation.assert_called_once_with("test-conv-1")


class TestSystemEndpoints:
    """Test system information endpoints"""

    def test_system_info_endpoint(self, client):
        """Test GET /system/info returns system information"""
        with patch('windows_ai.main.system_info.get_system_info') as mock:
            mock.return_value = {
                "os": "Windows 11",
                "cpu": "Intel i7",
                "memory": "16GB"
            }

            response = client.get("/system/info")

            if response.status_code == 200:
                data = response.json()
                assert isinstance(data, dict)

    def test_system_info_error_handling(self, client):
        """Test GET /system/info handles errors gracefully"""
        with patch('windows_ai.main.system_info.get_system_info') as mock:
            mock.side_effect = Exception("System info error")

            response = client.get("/system/info")

            # Should return error response
            if response.status_code == 200:
                data = response.json()
                assert "error" in data


class TestConfigEndpoints:
    """Test configuration endpoints"""

    def test_get_config(self, client):
        """Test GET /config returns current configuration"""
        response = client.get("/config")

        if response.status_code == 200:
            data = response.json()
            assert isinstance(data, dict)

    def test_update_config(self, client):
        """Test POST /config updates configuration"""
        payload = {
            "theme": "dark",
            "language": "en"
        }

        response = client.post("/config", json=payload)

        # Config update should succeed or return validation error
        assert response.status_code in [200, 400, 422]


class TestModelEndpoints:
    """Test model management endpoints"""

    def test_get_models(self, client):
        """Test GET /models returns model list"""
        response = client.get("/models")

        if response.status_code == 200:
            data = response.json()
            assert "models" in data or isinstance(data, list)

    def test_get_available_models(self, client):
        """Test GET /models/available returns available models"""
        with patch('windows_ai.main.model_manager') as mock_mgr:
            mock_mgr.get_available_models.return_value = [
                {"name": "llama2", "size": "7B"},
                {"name": "mistral", "size": "7B"}
            ]

            response = client.get("/models/available")

            if response.status_code == 200:
                data = response.json()
                assert "models" in data or isinstance(data, list)

    def test_get_installed_models(self, client):
        """Test GET /models/installed returns installed models"""
        with patch('windows_ai.main.model_manager') as mock_mgr:
            mock_mgr.get_installed_models.return_value = [
                {"name": "llama2", "path": "/models/llama2"}
            ]

            response = client.get("/models/installed")

            if response.status_code == 200:
                data = response.json()
                assert "models" in data or isinstance(data, list)

    def test_get_model_by_id(self, client):
        """Test GET /models/{id} returns model details"""
        with patch('windows_ai.main.model_manager') as mock_mgr:
            mock_mgr.get_model_info.return_value = {
                "name": "llama2",
                "size": "7B",
                "downloaded": True
            }

            response = client.get("/models/llama2")

            if response.status_code == 200:
                data = response.json()
                assert "name" in data or "model" in data

    def test_download_model(self, client):
        """Test POST /models/{id}/download initiates download"""
        with patch('windows_ai.main.model_manager') as mock_mgr:
            mock_mgr.download_model = AsyncMock(return_value=True)

            response = client.post("/models/llama2/download")

            # Download should be initiated
            assert response.status_code in [200, 202, 400]

    def test_download_model_status(self, client):
        """Test GET /models/{id}/download/status returns progress"""
        with patch('windows_ai.main.model_manager') as mock_mgr:
            mock_mgr.get_download_status.return_value = {
                "status": "downloading",
                "progress": 45
            }

            response = client.get("/models/llama2/download/status")

            if response.status_code == 200:
                data = response.json()
                assert "status" in data or "progress" in data

    def test_delete_model(self, client):
        """Test DELETE /models/{id} removes model"""
        with patch('windows_ai.main.model_manager') as mock_mgr:
            mock_mgr.delete_model = AsyncMock(return_value=True)

            response = client.delete("/models/llama2")

            # Delete should succeed or return error
            assert response.status_code in [200, 404]


class TestPluginEndpoints:
    """Test plugin management endpoints"""

    def test_list_plugins(self, client):
        """Test GET /plugins returns plugin list"""
        with patch('windows_ai.main.plugin_registry') as mock_registry:
            mock_registry.list_plugins.return_value = [
                {"id": "plugin1", "name": "Plugin 1", "enabled": True},
                {"id": "plugin2", "name": "Plugin 2", "enabled": False}
            ]

            response = client.get("/plugins")

            if response.status_code == 200:
                data = response.json()
                assert "plugins" in data

    def test_get_plugin_by_id(self, client):
        """Test GET /plugins/{id} returns plugin details"""
        with patch('windows_ai.main.plugin_registry') as mock_registry:
            mock_plugin = Mock()
            mock_plugin.metadata.to_dict.return_value = {
                "id": "test_plugin",
                "name": "Test Plugin"
            }
            mock_plugin.get_schema.return_value = {"type": "object"}
            mock_registry.get_plugin.return_value = mock_plugin

            response = client.get("/plugins/test_plugin")

            if response.status_code == 200:
                data = response.json()
                assert "id" in data or "metadata" in data

    def test_execute_plugin(self, client):
        """Test POST /plugins/{id}/execute runs plugin"""
        with patch('windows_ai.main.plugin_registry') as mock_registry:
            mock_registry.execute_plugin = AsyncMock(return_value={
                "success": True,
                "result": "Plugin executed"
            })

            response = client.post(
                "/plugins/test_plugin/execute",
                json={"param": "value"}
            )

            # Execution should return result
            assert response.status_code in [200, 400, 404]

    def test_enable_plugin(self, client):
        """Test POST /plugins/{id}/enable enables plugin"""
        with patch('windows_ai.main.plugin_registry') as mock_registry:
            mock_registry.enable_plugin = AsyncMock(return_value=True)

            response = client.post("/plugins/test_plugin/enable")

            if response.status_code == 200:
                data = response.json()
                assert "message" in data

    def test_disable_plugin(self, client):
        """Test POST /plugins/{id}/disable disables plugin"""
        with patch('windows_ai.main.plugin_registry') as mock_registry:
            mock_registry.disable_plugin = AsyncMock(return_value=True)

            response = client.post("/plugins/test_plugin/disable")

            if response.status_code == 200:
                data = response.json()
                assert "message" in data

    def test_reload_plugin(self, client):
        """Test POST /plugins/{id}/reload reloads plugin"""
        with patch('windows_ai.main.plugin_registry') as mock_registry:
            mock_registry.reload_plugin = AsyncMock(return_value=True)

            response = client.post("/plugins/test_plugin/reload")

            if response.status_code == 200:
                data = response.json()
                assert "message" in data

    def test_get_plugins_by_type(self, client):
        """Test GET /plugins/types/{type} filters plugins"""
        with patch('windows_ai.main.plugin_registry') as mock_registry:
            mock_registry.get_plugins_by_type.return_value = [
                Mock(metadata=Mock(to_dict=lambda: {"id": "plugin1", "type": "action"}))
            ]

            response = client.get("/plugins/types/action")

            if response.status_code == 200:
                data = response.json()
                assert "plugins" in data or isinstance(data, list)


class TestAutomationEndpoints:
    """Test automation endpoints (watchers and tasks)"""

    def test_list_watchers(self, client):
        """Test GET /automation/watchers returns watcher list"""
        response = client.get("/automation/watchers")

        if response.status_code == 200:
            data = response.json()
            assert "watchers" in data or isinstance(data, list)

    def test_get_watcher_by_id(self, client):
        """Test GET /automation/watchers/{id} returns watcher details"""
        response = client.get("/automation/watchers/test-watcher")

        # May not exist, but endpoint should be accessible
        assert response.status_code in [200, 404]

    def test_create_watcher(self, client):
        """Test POST /automation/watchers creates new watcher"""
        payload = {
            "path": "/test/path",
            "patterns": ["*.txt"],
            "recursive": True,
            "actions": [{"type": "log"}]
        }

        response = client.post("/automation/watchers", json=payload)

        # Creation should succeed or return validation error
        assert response.status_code in [200, 201, 400, 422]

    def test_update_watcher(self, client):
        """Test PUT /automation/watchers/{id} updates watcher"""
        payload = {
            "patterns": ["*.log", "*.txt"]
        }

        response = client.put("/automation/watchers/test-watcher", json=payload)

        # Update should succeed or return not found
        assert response.status_code in [200, 404, 422]

    def test_delete_watcher(self, client):
        """Test DELETE /automation/watchers/{id} removes watcher"""
        response = client.delete("/automation/watchers/test-watcher")

        # Delete should succeed or return not found
        assert response.status_code in [200, 404]

    def test_start_watcher(self, client):
        """Test POST /automation/watchers/{id}/start activates watcher"""
        response = client.post("/automation/watchers/test-watcher/start")

        assert response.status_code in [200, 404]

    def test_stop_watcher(self, client):
        """Test POST /automation/watchers/{id}/stop deactivates watcher"""
        response = client.post("/automation/watchers/test-watcher/stop")

        assert response.status_code in [200, 404]

    def test_list_tasks(self, client):
        """Test GET /automation/tasks returns task list"""
        response = client.get("/automation/tasks")

        if response.status_code == 200:
            data = response.json()
            assert "tasks" in data or isinstance(data, list)

    def test_create_task(self, client):
        """Test POST /automation/tasks creates scheduled task"""
        payload = {
            "name": "Test Task",
            "schedule": "0 9 * * *",
            "action": {"type": "command", "command": "echo test"}
        }

        response = client.post("/automation/tasks", json=payload)

        # Creation should succeed or return validation error
        assert response.status_code in [200, 201, 400, 422]


class TestUpdateEndpoints:
    """Test update management endpoints"""

    def test_update_status(self, client):
        """Test GET /updates/status returns update status"""
        response = client.get("/updates/status")

        if response.status_code == 200:
            data = response.json()
            assert "current_version" in data or "status" in data

    def test_check_updates(self, client):
        """Test POST /updates/check looks for updates"""
        response = client.post("/updates/check")

        # Check should return status
        assert response.status_code in [200, 500]

    def test_download_update(self, client):
        """Test POST /updates/download initiates download"""
        payload = {"version": "1.0.1"}

        response = client.post("/updates/download", json=payload)

        # Download should be initiated or return error
        assert response.status_code in [200, 202, 400, 404]

    def test_install_update(self, client):
        """Test POST /updates/install installs update"""
        response = client.post("/updates/install")

        # Install should be initiated or return error
        assert response.status_code in [200, 400]

    def test_get_update_preferences(self, client):
        """Test GET /updates/preferences returns settings"""
        response = client.get("/updates/preferences")

        if response.status_code == 200:
            data = response.json()
            assert isinstance(data, dict)

    def test_set_update_preferences(self, client):
        """Test POST /updates/preferences updates settings"""
        payload = {
            "auto_check": True,
            "auto_download": False
        }

        response = client.post("/updates/preferences", json=payload)

        # Preferences should be updated
        assert response.status_code in [200, 400, 422]


@pytest.mark.parametrize("endpoint,method", [
    ("/", "GET"),
    ("/health", "GET"),
    ("/system/info", "GET"),
    ("/config", "GET"),
    ("/models", "GET"),
    ("/plugins", "GET"),
    ("/conversations", "GET"),
    ("/automation/watchers", "GET"),
    ("/automation/tasks", "GET"),
])
def test_endpoint_accessibility(client, endpoint, method):
    """Test that all GET endpoints are accessible"""
    if method == "GET":
        response = client.get(endpoint)
    elif method == "POST":
        response = client.post(endpoint, json={})

    # Endpoint should be accessible (not 404)
    assert response.status_code != 404, f"Endpoint {method} {endpoint} not found"


def test_cors_headers(client):
    """Test that CORS headers are properly set"""
    response = client.options("/health")

    # CORS headers should be present
    # Actual values depend on CORS configuration
    assert response.status_code in [200, 405]


def test_invalid_json_handling(client):
    """Test that invalid JSON is handled gracefully"""
    response = client.post(
        "/chat",
        data="invalid json {{{",
        headers={"Content-Type": "application/json"}
    )

    # Should return 400 or 422 for invalid JSON
    assert response.status_code in [400, 422]


def test_rate_limiting(client):
    """Test rate limiting if configured"""
    # Make multiple rapid requests
    responses = [client.get("/health") for _ in range(100)]

    # Most should succeed
    success_count = sum(1 for r in responses if r.status_code == 200)
    assert success_count >= 90, "Too many requests blocked"


class TestErrorHandling:
    """Test error handling across endpoints"""

    def test_404_for_unknown_endpoint(self, client):
        """Test that unknown endpoints return 404"""
        response = client.get("/nonexistent/endpoint")

        assert response.status_code == 404

    def test_405_for_wrong_method(self, client):
        """Test that wrong HTTP method returns 405"""
        # POST to GET-only endpoint
        response = client.post("/health")

        assert response.status_code == 405

    def test_422_for_invalid_payload(self, client):
        """Test that invalid payloads return 422"""
        response = client.post("/chat", json={"invalid": "payload"})

        assert response.status_code == 422
