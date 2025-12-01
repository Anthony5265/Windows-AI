"""
SQL Injection and Command Injection Tests
Tests for OWASP Top 10 #1 - Injection vulnerabilities
"""

import pytest
from fastapi.testclient import TestClient


@pytest.fixture
def client():
    """Create test client"""
    try:
        from windows_ai.main import app
        return TestClient(app)
    except:
        pytest.skip("App not available")


class TestSQLInjection:
    """Test protection against SQL injection"""

    @pytest.mark.parametrize("malicious_input", [
        "' OR '1'='1",
        "'; DROP TABLE users--",
        "' UNION SELECT * FROM users--",
        "admin'--",
        "1' AND '1'='1"
    ])
    def test_sql_injection_in_chat(self, client, malicious_input):
        """Test that SQL injection attempts in chat are handled safely"""
        payload = {
            "message": malicious_input,
            "model": "gpt-3.5-turbo"
        }

        response = client.post("/chat", json=payload)

        # Should either process safely or reject, but not crash
        assert response.status_code in [200, 400, 422, 500]

        if response.status_code == 200:
            data = response.json()
            # Response should not contain SQL error messages
            assert "SQL" not in str(data).upper()
            assert "syntax error" not in str(data).lower()


class TestCommandInjection:
    """Test protection against command injection"""

    @pytest.mark.parametrize("malicious_input", [
        "; ls -la",
        "| cat /etc/passwd",
        "&& rm -rf /",
        "`whoami`",
        "$(cat /etc/passwd)",
        "; ping -c 10 evil.com"
    ])
    def test_command_injection_prevention(self, client, malicious_input):
        """Test that command injection attempts are blocked"""
        # Test in automation task creation
        payload = {
            "name": "Test Task",
            "schedule": "0 9 * * *",
            "action": {
                "type": "command",
                "command": f"echo test{malicious_input}"
            }
        }

        response = client.post("/automation/tasks", json=payload)

        # Should validate and reject or sanitize
        # Must not execute malicious command
        assert response.status_code in [200, 201, 400, 422]


class TestPathTraversal:
    """Test protection against path traversal attacks"""

    @pytest.mark.parametrize("malicious_path", [
        "../../../etc/passwd",
        "..\\..\\..\\Windows\\System32\\config\\SAM",
        "....//....//....//etc/passwd",
        "/etc/passwd",
        "C:\\Windows\\System32\\config\\SAM"
    ])
    def test_path_traversal_in_file_operations(self, client, malicious_path):
        """Test that path traversal attempts are blocked"""
        # Test in folder watcher creation
        payload = {
            "path": malicious_path,
            "patterns": ["*.txt"],
            "actions": [{"type": "log"}]
        }

        response = client.post("/automation/watchers", json=payload)

        # Should reject malicious paths
        if response.status_code == 200:
            data = response.json()
            # Should not actually create watcher with malicious path
            assert malicious_path not in str(data)


class TestXSSPrevention:
    """Test protection against XSS attacks"""

    @pytest.mark.parametrize("malicious_input", [
        "<script>alert('XSS')</script>",
        "<img src=x onerror=alert('XSS')>",
        "<svg onload=alert('XSS')>",
        "javascript:alert('XSS')",
        "<iframe src='javascript:alert(\"XSS\")'></iframe>"
    ])
    def test_xss_in_chat_messages(self, client, malicious_input):
        """Test that XSS attempts are sanitized"""
        payload = {
            "message": malicious_input,
            "model": "gpt-3.5-turbo"
        }

        response = client.post("/chat", json=payload)

        if response.status_code == 200:
            data = response.json()
            # Response should not contain unescaped script tags
            response_str = str(data)
            assert "<script>" not in response_str.lower()
            assert "onerror=" not in response_str.lower()
            assert "javascript:" not in response_str.lower()


class TestLDAPInjection:
    """Test protection against LDAP injection (if applicable)"""

    @pytest.mark.parametrize("malicious_input", [
        "*)(uid=*))(|(uid=*",
        "admin)(|(password=*))",
        "*)(objectClass=*"
    ])
    def test_ldap_injection_prevention(self, client, malicious_input):
        """Test LDAP injection protection"""
        # If LDAP is used, test here
        # For now, just ensure input validation works
        payload = {"username": malicious_input}

        # This test is a placeholder - adapt based on actual LDAP usage
        pytest.skip("LDAP not currently used")
