"""
Tests for remaining ROADMAP items: plugin sandbox, plugin pre-warming,
API profiler, expanded Matter adapter, RBAC verification, and credential rotation.
"""
import pytest
import asyncio
import time


# ========================================================================
# Matter Protocol Adapter (expanded)
# ========================================================================

class TestMatterAdapter:
    """Test expanded Matter protocol adapter."""

    def test_import(self):
        from iot.matter import MatterAdapter
        assert MatterAdapter is not None

    def test_create_adapter(self):
        from iot.matter import MatterAdapter
        adapter = MatterAdapter()
        assert adapter.protocol == "matter"
        assert adapter.fabric_id is not None

    def test_create_with_fabric_id(self):
        from iot.matter import MatterAdapter
        adapter = MatterAdapter(fabric_id="test-fabric-123")
        assert adapter.fabric_id == "test-fabric-123"

    def test_discover_empty(self):
        from iot.matter import MatterAdapter
        adapter = MatterAdapter()
        devices = adapter.discover()
        assert isinstance(devices, list)
        assert len(devices) == 0  # No commissioned devices yet

    def test_commission_device(self):
        from iot.matter import MatterAdapter, MatterDeviceType
        adapter = MatterAdapter()
        result = adapter.commission_device(
            setup_code="12345678901",
            device_name="Test Light",
            device_type=MatterDeviceType.LIGHT,
        )
        assert result["status"] == "success"
        assert result["node_id"] == 1
        assert result["device_type"] == "light"

    def test_commission_invalid_code(self):
        from iot.matter import MatterAdapter
        adapter = MatterAdapter()
        result = adapter.commission_device(setup_code="short")
        assert result["status"] == "error"

    def test_decommission_device(self):
        from iot.matter import MatterAdapter
        adapter = MatterAdapter()
        adapter.commission_device("12345678901", "Test")
        result = adapter.decommission_device(1)
        assert result["status"] == "success"

    def test_decommission_nonexistent(self):
        from iot.matter import MatterAdapter
        adapter = MatterAdapter()
        result = adapter.decommission_device(999)
        assert result["status"] == "error"

    def test_discover_after_commission(self):
        from iot.matter import MatterAdapter
        adapter = MatterAdapter()
        adapter.commission_device("12345678901", "My Light")
        devices = adapter.discover()
        assert len(devices) == 1
        assert devices[0].name == "My Light"
        assert devices[0].protocol == "matter"

    def test_send_on_off_command(self):
        from iot.matter import MatterAdapter
        adapter = MatterAdapter()
        adapter.commission_device("12345678901", "Light")
        result = adapter.send_command(1, "on_off", "on")
        assert result["status"] == "success"
        assert result["on_off"] is True

    def test_send_toggle_command(self):
        from iot.matter import MatterAdapter
        adapter = MatterAdapter()
        adapter.commission_device("12345678901", "Light")
        adapter.send_command(1, "on_off", "on")
        result = adapter.send_command(1, "on_off", "toggle")
        assert result["status"] == "success"
        assert result["on_off"] is False

    def test_send_level_command(self):
        from iot.matter import MatterAdapter
        adapter = MatterAdapter()
        adapter.commission_device("12345678901", "Dimmer")
        result = adapter.send_command(1, "level_control", "move_to_level", level=128)
        assert result["status"] == "success"
        assert result["level"] == 128

    def test_thermostat_command(self):
        from iot.matter import MatterAdapter
        adapter = MatterAdapter()
        adapter.commission_device("12345678901", "Thermostat")
        result = adapter.send_command(1, "thermostat", "set_heating_setpoint", temperature=22.5)
        assert result["status"] == "success"

    def test_send_command_unknown_node(self):
        from iot.matter import MatterAdapter
        adapter = MatterAdapter()
        result = adapter.send_command(999, "on_off", "on")
        assert result["status"] == "error"

    def test_read_attribute(self):
        from iot.matter import MatterAdapter
        adapter = MatterAdapter()
        adapter.commission_device("12345678901", "Light")
        adapter.send_command(1, "on_off", "on")
        result = adapter.read_attribute(1, "on_off", "state")
        assert result["status"] == "success"
        assert result["value"] is True

    def test_get_node_info(self):
        from iot.matter import MatterAdapter, MatterDeviceType
        adapter = MatterAdapter()
        adapter.commission_device("12345678901", "My Bulb", MatterDeviceType.LIGHT)
        info = adapter.get_node_info(1)
        assert info["status"] == "success"
        assert info["name"] == "My Bulb"
        assert info["device_type"] == "light"

    def test_subscribe_unsubscribe(self):
        from iot.matter import MatterAdapter
        adapter = MatterAdapter()
        adapter.commission_device("12345678901", "Sensor")
        sub = adapter.subscribe(1, "temperature", "current_value")
        assert sub["status"] == "success"
        unsub = adapter.unsubscribe(1, "temperature", "current_value")
        assert unsub["status"] == "success"

    def test_get_fabric_info(self):
        from iot.matter import MatterAdapter
        adapter = MatterAdapter()
        adapter.commission_device("12345678901", "Light1")
        adapter.commission_device("12345678902", "Light2")
        info = adapter.get_fabric_info()
        assert info["status"] == "success"
        assert info["node_count"] == 2

    def test_pair_device(self):
        from iot.matter import MatterAdapter
        from iot.models import Device
        adapter = MatterAdapter()
        device = Device(id="test-1", name="Test Device", protocol="matter")
        assert adapter.pair(device) is True

    def test_device_types_enum(self):
        from iot.matter import MatterDeviceType
        assert MatterDeviceType.LIGHT.value == "light"
        assert MatterDeviceType.THERMOSTAT.value == "thermostat"
        assert MatterDeviceType.DOOR_LOCK.value == "door_lock"

    def test_fabric_state_enum(self):
        from iot.matter import MatterFabricState
        assert MatterFabricState.IDLE.value == "idle"
        assert MatterFabricState.OPERATIONAL.value == "operational"


# ========================================================================
# Plugin Sandbox
# ========================================================================

class TestPluginSandbox:
    """Test plugin sandbox isolation."""

    def test_import(self):
        from windows_ai.security.plugin_sandbox import PluginSandbox, SandboxLevel, SandboxPolicy
        assert PluginSandbox is not None
        assert SandboxLevel is not None

    def test_sandbox_levels(self):
        from windows_ai.security.plugin_sandbox import SandboxLevel
        assert SandboxLevel.NONE.value == "none"
        assert SandboxLevel.MINIMAL.value == "minimal"
        assert SandboxLevel.STANDARD.value == "standard"
        assert SandboxLevel.STRICT.value == "strict"
        assert SandboxLevel.MAXIMUM.value == "maximum"

    def test_execute_no_sandbox(self):
        from windows_ai.security.plugin_sandbox import PluginSandbox, SandboxPolicy, SandboxLevel
        sandbox = PluginSandbox(SandboxPolicy(level=SandboxLevel.NONE))
        result = sandbox.execute(lambda: 42)
        assert result.success is True
        assert result.result == 42

    def test_execute_with_import_guard(self):
        from windows_ai.security.plugin_sandbox import PluginSandbox, SandboxPolicy, SandboxLevel

        sandbox = PluginSandbox(SandboxPolicy(level=SandboxLevel.MINIMAL))

        def safe_func():
            import json
            return json.dumps({"ok": True})

        result = sandbox.execute(safe_func)
        assert result.success is True

    def test_blocked_import(self):
        from windows_ai.security.plugin_sandbox import PluginSandbox, SandboxPolicy, SandboxLevel

        sandbox = PluginSandbox(SandboxPolicy(
            level=SandboxLevel.STANDARD,
            blocked_imports={"_this_module_does_not_exist"},
        ))

        def bad_func():
            import _this_module_does_not_exist
            return _this_module_does_not_exist

        result = sandbox.execute(bad_func)
        assert result.success is False
        assert len(result.violations) > 0

    def test_execution_timing(self):
        from windows_ai.security.plugin_sandbox import PluginSandbox, SandboxPolicy, SandboxLevel
        sandbox = PluginSandbox(SandboxPolicy(level=SandboxLevel.MINIMAL))
        result = sandbox.execute(lambda: time.sleep(0.01) or "done")
        assert result.success is True
        assert result.execution_time_ms >= 5  # at least 5ms

    def test_exception_handling(self):
        from windows_ai.security.plugin_sandbox import PluginSandbox, SandboxPolicy, SandboxLevel
        sandbox = PluginSandbox(SandboxPolicy(level=SandboxLevel.STANDARD))
        result = sandbox.execute(lambda: 1 / 0)
        assert result.success is False
        assert "division by zero" in result.error

    def test_check_path_access(self):
        from windows_ai.security.plugin_sandbox import PluginSandbox, SandboxPolicy, SandboxLevel
        sandbox = PluginSandbox(SandboxPolicy(level=SandboxLevel.STANDARD))
        assert sandbox.check_path_access("/tmp/safe") is True
        assert sandbox.check_path_access("/etc/passwd") is False

    def test_check_path_no_sandbox(self):
        from windows_ai.security.plugin_sandbox import PluginSandbox, SandboxPolicy, SandboxLevel
        sandbox = PluginSandbox(SandboxPolicy(level=SandboxLevel.NONE))
        assert sandbox.check_path_access("/etc/passwd") is True

    def test_check_network_access(self):
        from windows_ai.security.plugin_sandbox import PluginSandbox, SandboxPolicy, SandboxLevel
        sandbox = PluginSandbox(SandboxPolicy(
            level=SandboxLevel.STANDARD,
            network_allowlist=["api.openai.com"],
        ))
        assert sandbox.check_network_access("api.openai.com") is True
        assert sandbox.check_network_access("evil.example.com") is False

    def test_network_disabled(self):
        from windows_ai.security.plugin_sandbox import PluginSandbox, SandboxPolicy, SandboxLevel
        sandbox = PluginSandbox(SandboxPolicy(
            level=SandboxLevel.MAXIMUM,
            network_allowed=False,
        ))
        assert sandbox.check_network_access("anything") is False

    def test_policy_summary(self):
        from windows_ai.security.plugin_sandbox import PluginSandbox, SandboxPolicy, SandboxLevel
        sandbox = PluginSandbox(SandboxPolicy(level=SandboxLevel.STRICT))
        summary = sandbox.get_policy_summary()
        assert summary["level"] == "strict"
        assert "blocked_imports" in summary
        assert isinstance(summary["blocked_imports"], list)


# ========================================================================
# Plugin Pre-Warming
# ========================================================================

class TestPluginPreWarmer:
    """Test background plugin pre-warming."""

    def test_import(self):
        from windows_ai.core.plugin_prewarmer import PluginPreWarmer
        assert PluginPreWarmer is not None

    def test_create_warmer(self):
        from windows_ai.core.plugin_prewarmer import PluginPreWarmer
        warmer = PluginPreWarmer()
        assert warmer is not None

    def test_record_usage(self):
        from windows_ai.core.plugin_prewarmer import PluginPreWarmer
        warmer = PluginPreWarmer()
        warmer.record_usage("plugin-a")
        warmer.record_usage("plugin-a")
        warmer.record_usage("plugin-b")
        popular = warmer.get_popular(top_k=2)
        assert popular[0] == "plugin-a"

    @pytest.mark.asyncio
    async def test_warm_plugin(self):
        from windows_ai.core.plugin_prewarmer import PluginPreWarmer
        warmer = PluginPreWarmer()
        result = await warmer.warm_plugin("test-plugin")
        assert result.success is True
        assert warmer.is_warmed("test-plugin")

    @pytest.mark.asyncio
    async def test_warm_already_warmed(self):
        from windows_ai.core.plugin_prewarmer import PluginPreWarmer
        warmer = PluginPreWarmer()
        await warmer.warm_plugin("p1")
        result = await warmer.warm_plugin("p1")
        assert result.success is True
        assert result.load_time_ms == 0.0  # Instant because already warmed

    @pytest.mark.asyncio
    async def test_warm_plugins_batch(self):
        from windows_ai.core.plugin_prewarmer import PluginPreWarmer
        warmer = PluginPreWarmer()
        stats = await warmer.warm_plugins(["p1", "p2", "p3"])
        assert stats.total == 3
        assert stats.succeeded == 3
        assert stats.total_time_ms >= 0

    @pytest.mark.asyncio
    async def test_warm_popular(self):
        from windows_ai.core.plugin_prewarmer import PluginPreWarmer
        warmer = PluginPreWarmer()
        warmer.record_usage("popular-1")
        warmer.record_usage("popular-1")
        warmer.record_usage("popular-2")
        stats = await warmer.warm_popular(top_k=5)
        assert stats.succeeded >= 2

    def test_get_stats(self):
        from windows_ai.core.plugin_prewarmer import PluginPreWarmer
        warmer = PluginPreWarmer()
        stats = warmer.get_stats()
        assert stats["warmed_count"] == 0
        assert stats["usage_tracked"] == 0

    def test_reset(self):
        from windows_ai.core.plugin_prewarmer import PluginPreWarmer
        warmer = PluginPreWarmer()
        warmer.record_usage("p1")
        warmer.reset()
        assert warmer.get_stats()["warmed_count"] == 0
        assert warmer.get_stats()["usage_tracked"] == 0


# ========================================================================
# API Profiler
# ========================================================================

class TestAPIProfiler:
    """Test API performance profiling."""

    def test_import(self):
        from windows_ai.core.api_profiler import APIProfiler
        assert APIProfiler is not None

    def test_create_profiler(self):
        from windows_ai.core.api_profiler import APIProfiler
        profiler = APIProfiler()
        assert profiler is not None

    def test_record_request(self):
        from windows_ai.core.api_profiler import APIProfiler
        profiler = APIProfiler()
        profiler.record_request("/api/chat", "POST", latency_ms=42.0)
        stats = profiler.get_endpoint_stats("/api/chat", "POST")
        assert stats is not None
        assert stats["request_count"] == 1
        assert stats["avg_ms"] == 42.0

    def test_multiple_requests(self):
        from windows_ai.core.api_profiler import APIProfiler
        profiler = APIProfiler()
        for i in range(10):
            profiler.record_request("/api/test", "GET", latency_ms=float(i * 10))
        stats = profiler.get_endpoint_stats("/api/test", "GET")
        assert stats["request_count"] == 10
        assert stats["min_ms"] == 0.0
        assert stats["max_ms"] == 90.0

    def test_p95_calculation(self):
        from windows_ai.core.api_profiler import APIProfiler
        profiler = APIProfiler()
        for i in range(100):
            profiler.record_request("/api/p95", "GET", latency_ms=float(i))
        stats = profiler.get_endpoint_stats("/api/p95", "GET")
        assert stats["p95_ms"] >= 90.0  # 95th percentile of 0-99

    def test_error_tracking(self):
        from windows_ai.core.api_profiler import APIProfiler
        profiler = APIProfiler()
        profiler.record_request("/api/fail", "POST", latency_ms=10, status_code=500)
        stats = profiler.get_endpoint_stats("/api/fail", "POST")
        assert stats["error_count"] == 1

    def test_get_all_endpoints(self):
        from windows_ai.core.api_profiler import APIProfiler
        profiler = APIProfiler()
        profiler.record_request("/api/a", "GET", latency_ms=10)
        profiler.record_request("/api/b", "POST", latency_ms=20)
        all_eps = profiler.get_all_endpoints()
        assert len(all_eps) == 2

    def test_get_slow_endpoints(self):
        from windows_ai.core.api_profiler import APIProfiler
        profiler = APIProfiler()
        profiler.record_request("/api/fast", "GET", latency_ms=10)
        profiler.record_request("/api/slow", "GET", latency_ms=500)
        slow = profiler.get_slow_endpoints(threshold_ms=200)
        assert len(slow) == 1
        assert slow[0]["path"] == "/api/slow"

    def test_get_summary(self):
        from windows_ai.core.api_profiler import APIProfiler
        profiler = APIProfiler()
        for i in range(50):
            profiler.record_request("/api/test", "GET", latency_ms=float(i))
        summary = profiler.get_summary()
        assert summary["total_requests"] == 50
        assert "global_avg_ms" in summary
        assert "global_p95_ms" in summary

    def test_memory_usage(self):
        from windows_ai.core.api_profiler import APIProfiler
        profiler = APIProfiler()
        mem = profiler.get_memory_usage()
        assert "status" in mem
        if mem["status"] == "success":
            assert "rss_mb" in mem
            assert "within_target" in mem

    def test_reset(self):
        from windows_ai.core.api_profiler import APIProfiler
        profiler = APIProfiler()
        profiler.record_request("/api/x", "GET", latency_ms=10)
        profiler.reset()
        assert profiler.get_all_endpoints() == []


# ========================================================================
# RBAC Verification
# ========================================================================

class TestAdvancedRBAC:
    """Test RBAC system."""

    def test_import(self):
        from windows_ai.security.advanced_rbac import AdvancedRBAC, PermissionLevel, ResourceType
        assert AdvancedRBAC is not None

    def test_create_rbac(self):
        from windows_ai.security.advanced_rbac import AdvancedRBAC
        rbac = AdvancedRBAC()
        assert rbac is not None

    def test_permission_levels(self):
        from windows_ai.security.advanced_rbac import PermissionLevel
        assert PermissionLevel.READ.value == "read"
        assert PermissionLevel.WRITE.value == "write"
        assert PermissionLevel.DELETE.value == "delete"
        assert PermissionLevel.ADMIN.value == "admin"

    def test_resource_types(self):
        from windows_ai.security.advanced_rbac import ResourceType
        assert ResourceType.QUERY.value == "query"
        assert ResourceType.PLUGIN.value == "plugin"
        assert ResourceType.CONFIGURATION.value == "configuration"

    def test_permission_matching(self):
        from windows_ai.security.advanced_rbac import Permission, PermissionLevel, ResourceType
        perm = Permission(
            permission_id="p1",
            resource_type=ResourceType.PLUGIN,
            level=PermissionLevel.READ,
        )
        assert perm.matches(ResourceType.PLUGIN, PermissionLevel.READ) is True
        assert perm.matches(ResourceType.QUERY, PermissionLevel.READ) is False

    def test_create_role(self):
        from windows_ai.security.advanced_rbac import (
            AdvancedRBAC, Role
        )
        rbac = AdvancedRBAC()
        role = Role(
            role_id="viewer",
            name="Viewer",
            description="Read-only access",
            permissions={"query:read", "plugin:read"},
        )
        assert role.role_id == "viewer"
        assert len(role.permissions) == 2


# ========================================================================
# Credential Rotation Scheduler
# ========================================================================

class TestCredentialRotation:
    """Test credential rotation scheduler."""

    def test_import(self):
        from windows_ai.security.credential_rotation_scheduler import CredentialRotationScheduler
        assert CredentialRotationScheduler is not None

    def test_rotation_status_enum(self):
        from windows_ai.security.credential_rotation_scheduler import RotationStatus
        assert RotationStatus is not None

    def test_credential_type_enum(self):
        from windows_ai.security.credential_rotation_scheduler import CredentialType
        assert CredentialType is not None

    def test_create_scheduler(self):
        from windows_ai.security.credential_rotation_scheduler import CredentialRotationScheduler
        scheduler = CredentialRotationScheduler()
        assert scheduler is not None


# ========================================================================
# Existing Modules — Additional Coverage
# ========================================================================

class TestProviderFailover:
    """Additional tests for provider failover."""

    def test_import(self):
        from windows_ai.core.provider_failover import ProviderFailover
        assert ProviderFailover is not None

    def test_create_failover(self):
        from windows_ai.core.provider_failover import ProviderFailover
        pf = ProviderFailover()
        assert pf is not None


class TestPluginDependencyResolver:
    """Additional tests for dependency resolver."""

    def test_import(self):
        from windows_ai.plugins.dependency_resolver import PluginDependencyResolver
        assert PluginDependencyResolver is not None

    def test_resolve_empty(self):
        from windows_ai.plugins.dependency_resolver import PluginDependencyResolver
        resolver = PluginDependencyResolver()
        # No plugins registered → empty order
        order = resolver.resolve()
        assert order == []

    def test_resolve_simple(self):
        from windows_ai.plugins.dependency_resolver import PluginDependencyResolver
        resolver = PluginDependencyResolver()
        resolver.register("B", depends_on=[])
        resolver.register("A", depends_on=["B"])
        order = resolver.resolve()
        assert order.index("B") < order.index("A")


class TestLazyLoader:
    """Additional tests for lazy manager loader."""

    def test_import(self):
        from windows_ai.core.lazy_loader import LazyManagerLoader
        assert LazyManagerLoader is not None


class TestCrashRecovery:
    """Additional tests for crash recovery."""

    def test_import(self):
        from windows_ai.core.crash_recovery import CrashRecoveryManager
        assert CrashRecoveryManager is not None


class TestPluginSearchIndex:
    """Additional tests for plugin search."""

    def test_import(self):
        from windows_ai.search.plugin_search import PluginSearchIndex
        assert PluginSearchIndex is not None

    def test_index_and_search(self):
        from windows_ai.search.plugin_search import PluginSearchIndex
        idx = PluginSearchIndex()
        idx.index_plugin({"id": "audio-transcription", "name": "Audio Transcription", "description": "Transcribe audio files"})
        results = idx.search("audio", top_k=5)
        assert len(results) >= 1
