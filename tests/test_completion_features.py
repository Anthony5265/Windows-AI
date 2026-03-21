"""
Tests for new completion features:
- Observability (tracing, metrics, structured logging)
- CLI commands
- Expanded mesh agent coordinator
- Plugin sandbox enforcement
"""
import pytest
import asyncio
import time
import json
import os
import tempfile


# ========================================================================
# Observability: Tracing
# ========================================================================

class TestTracer:
    """Tests for distributed tracing."""

    def test_start_span_basic(self):
        from windows_ai.observability.tracing import Tracer
        tracer = Tracer(service_name="test-svc")
        with tracer.start_span("test_op") as span:
            span.set_attribute("key", "value")
        assert span.end_time is not None
        assert span.duration_ms >= 0
        assert span.attributes["key"] == "value"
        assert span.status == "ok"

    def test_nested_spans_share_trace_id(self):
        from windows_ai.observability.tracing import Tracer
        tracer = Tracer()
        with tracer.start_span("parent") as parent:
            with tracer.start_span("child") as child:
                pass
        assert parent.context.trace_id == child.context.trace_id
        assert child.context.parent_span_id == parent.context.span_id

    def test_span_error_handling(self):
        from windows_ai.observability.tracing import Tracer
        tracer = Tracer()
        try:
            with tracer.start_span("failing") as span:
                raise ValueError("test error")
        except ValueError:
            pass
        assert span.status == "error"
        assert "test error" in span.status_message
        assert len(span.events) == 1
        assert span.events[0].name == "exception"

    def test_add_event(self):
        from windows_ai.observability.tracing import Tracer
        tracer = Tracer()
        with tracer.start_span("evented") as span:
            span.add_event("checkpoint", {"step": 1})
            span.add_event("checkpoint", {"step": 2})
        assert len(span.events) == 2

    def test_get_recent_spans(self):
        from windows_ai.observability.tracing import Tracer
        tracer = Tracer()
        for i in range(5):
            with tracer.start_span(f"op_{i}"):
                pass
        recent = tracer.get_recent_spans(limit=3)
        assert len(recent) == 3

    def test_get_trace_by_id(self):
        from windows_ai.observability.tracing import Tracer
        tracer = Tracer()
        with tracer.start_span("traced") as span:
            pass
        trace = tracer.get_trace(span.context.trace_id)
        assert len(trace) >= 1

    def test_get_error_spans(self):
        from windows_ai.observability.tracing import Tracer
        tracer = Tracer()
        try:
            with tracer.start_span("bad"):
                raise RuntimeError("boom")
        except RuntimeError:
            pass
        errors = tracer.get_error_spans()
        assert len(errors) == 1

    def test_clear_spans(self):
        from windows_ai.observability.tracing import Tracer
        tracer = Tracer()
        with tracer.start_span("x"):
            pass
        count = tracer.clear()
        assert count >= 1
        assert tracer.get_recent_spans() == []

    def test_stats(self):
        from windows_ai.observability.tracing import Tracer
        tracer = Tracer(service_name="stats-test")
        with tracer.start_span("op"):
            pass
        stats = tracer.stats()
        assert stats["service_name"] == "stats-test"
        assert stats["total_spans"] == 1

    def test_span_context_serialization(self):
        from windows_ai.observability.tracing import SpanContext
        ctx = SpanContext(trace_id="abc", span_id="def", parent_span_id="ghi")
        d = ctx.to_dict()
        ctx2 = SpanContext.from_dict(d)
        assert ctx2.trace_id == "abc"
        assert ctx2.parent_span_id == "ghi"

    def test_exporter_callback(self):
        from windows_ai.observability.tracing import Tracer
        tracer = Tracer()
        exported = []
        tracer.add_exporter(lambda s: exported.append(s))
        with tracer.start_span("exported"):
            pass
        assert len(exported) == 1


# ========================================================================
# Observability: Metrics
# ========================================================================

class TestMetrics:
    """Tests for metrics collection."""

    def test_counter(self):
        from windows_ai.observability.metrics import MetricsCollector
        mc = MetricsCollector()
        c = mc.counter("requests_total", "Total requests")
        c.inc()
        c.inc(5)
        assert c.value == 6

    def test_counter_reset(self):
        from windows_ai.observability.metrics import MetricsCollector
        mc = MetricsCollector()
        c = mc.counter("test")
        c.inc(10)
        c.reset()
        assert c.value == 0

    def test_gauge(self):
        from windows_ai.observability.metrics import MetricsCollector
        mc = MetricsCollector()
        g = mc.gauge("memory_usage", "Memory usage")
        g.set(500)
        assert g.value == 500
        g.inc(100)
        assert g.value == 600
        g.dec(50)
        assert g.value == 550

    def test_histogram(self):
        from windows_ai.observability.metrics import MetricsCollector
        mc = MetricsCollector()
        h = mc.histogram("latency", "Request latency")
        for val in [0.01, 0.05, 0.1, 0.5, 1.0, 2.0]:
            h.observe(val)
        assert h.count == 6
        assert h.sum > 0
        assert h.mean > 0

    def test_histogram_percentile(self):
        from windows_ai.observability.metrics import MetricsCollector
        mc = MetricsCollector()
        h = mc.histogram("latency")
        for val in [0.01, 0.02, 0.03, 0.04, 0.05, 0.1, 0.2, 0.5, 1.0, 5.0]:
            h.observe(val)
        p50 = h.percentile(50)
        p99 = h.percentile(99)
        assert p50 <= p99

    def test_get_all_metrics(self):
        from windows_ai.observability.metrics import MetricsCollector
        mc = MetricsCollector()
        mc.counter("c1").inc()
        mc.gauge("g1").set(42)
        mc.histogram("h1").observe(0.5)
        all_metrics = mc.get_all()
        assert "c1" in all_metrics["counters"]
        assert "g1" in all_metrics["gauges"]
        assert "h1" in all_metrics["histograms"]

    def test_get_same_metric(self):
        from windows_ai.observability.metrics import MetricsCollector
        mc = MetricsCollector()
        c1 = mc.counter("test")
        c2 = mc.counter("test")
        assert c1 is c2

    def test_stats(self):
        from windows_ai.observability.metrics import MetricsCollector
        mc = MetricsCollector()
        mc.counter("c").inc()
        mc.gauge("g").set(1)
        stats = mc.stats()
        assert stats["total_metrics"] == 2


# ========================================================================
# Observability: Structured Logging
# ========================================================================

class TestStructuredLogging:
    """Tests for structured logging."""

    def test_basic_logging(self):
        from windows_ai.observability.structured_logging import StructuredLogger
        slog = StructuredLogger(service="test", output="none")
        entry = slog.info("Hello", key="value")
        assert entry["message"] == "Hello"
        assert entry["key"] == "value"
        assert entry["level"] == "INFO"

    def test_levels(self):
        from windows_ai.observability.structured_logging import StructuredLogger
        slog = StructuredLogger(output="none")
        d = slog.debug("debug msg")
        i = slog.info("info msg")
        w = slog.warning("warn msg")
        e = slog.error("err msg")
        c = slog.critical("crit msg")
        assert i["level"] == "INFO"
        assert e["level"] == "ERROR"

    def test_context_propagation(self):
        from windows_ai.observability.structured_logging import StructuredLogger
        slog = StructuredLogger(output="none")
        with slog.context(request_id="req-123"):
            entry = slog.info("inside context")
            assert entry.get("request_id") == "req-123"
        entry2 = slog.info("outside context")
        assert "request_id" not in entry2

    def test_nested_context(self):
        from windows_ai.observability.structured_logging import StructuredLogger
        slog = StructuredLogger(output="none")
        with slog.context(a="1"):
            with slog.context(b="2"):
                entry = slog.info("nested")
                assert entry.get("a") == "1"
                assert entry.get("b") == "2"
            entry2 = slog.info("outer")
            assert entry2.get("a") == "1"
            assert "b" not in entry2

    def test_get_entries(self):
        from windows_ai.observability.structured_logging import StructuredLogger
        slog = StructuredLogger(output="none")
        slog.info("msg1")
        slog.error("msg2")
        entries = slog.get_entries(limit=10)
        assert len(entries) == 2

    def test_get_errors(self):
        from windows_ai.observability.structured_logging import StructuredLogger
        slog = StructuredLogger(output="none")
        slog.info("ok")
        slog.error("bad")
        slog.critical("worse")
        errors = slog.get_errors()
        assert len(errors) == 2

    def test_search(self):
        from windows_ai.observability.structured_logging import StructuredLogger
        slog = StructuredLogger(output="none")
        slog.info("user login successful")
        slog.info("file uploaded")
        results = slog.search("login")
        assert len(results) == 1

    def test_clear(self):
        from windows_ai.observability.structured_logging import StructuredLogger
        slog = StructuredLogger(output="none")
        slog.info("x")
        slog.info("y")
        cleared = slog.clear()
        assert cleared == 2
        assert slog.get_entries() == []

    def test_stats(self):
        from windows_ai.observability.structured_logging import StructuredLogger
        slog = StructuredLogger(output="none", service="test-svc")
        slog.info("a")
        slog.error("b")
        stats = slog.stats()
        assert stats["service"] == "test-svc"
        assert stats["total_entries"] == 2
        assert stats["level_breakdown"]["INFO"] == 1
        assert stats["level_breakdown"]["ERROR"] == 1

    def test_callback(self):
        from windows_ai.observability.structured_logging import StructuredLogger
        slog = StructuredLogger(output="none")
        captured = []
        slog.add_callback(lambda e: captured.append(e))
        slog.info("callback test")
        assert len(captured) == 1

    def test_min_level_filtering(self):
        from windows_ai.observability.structured_logging import StructuredLogger
        slog = StructuredLogger(output="none", min_level="WARNING")
        d = slog.debug("skip this")
        i = slog.info("skip this too")
        w = slog.warning("keep this")
        assert d == {}
        assert i == {}
        assert w["level"] == "WARNING"


# ========================================================================
# CLI Commands
# ========================================================================

class TestCLICommands:
    """Tests for CLI command runner."""

    def test_help_command(self):
        from windows_ai.cli.commands import CLIRunner
        cli = CLIRunner()
        result = cli.run(["help"])
        assert result["status"] == "success"
        assert "commands" in result
        assert "help" in result["commands"]

    def test_version_command(self):
        from windows_ai.cli.commands import CLIRunner
        cli = CLIRunner()
        result = cli.run(["version"])
        assert result["status"] == "success"
        assert "version" in result

    def test_status_command(self):
        from windows_ai.cli.commands import CLIRunner
        cli = CLIRunner()
        result = cli.run(["status"])
        assert result["status"] == "success"
        assert "system" in result
        assert "cpu_percent" in result["system"]

    def test_health_command(self):
        from windows_ai.cli.commands import CLIRunner
        cli = CLIRunner()
        result = cli.run(["health"])
        assert result["status"] in ("success", "degraded")
        assert "checks" in result
        assert "python_version" in result["checks"]

    def test_benchmark_command(self):
        from windows_ai.cli.commands import CLIRunner
        cli = CLIRunner()
        result = cli.run(["diag:benchmark"])
        assert result["status"] == "success"
        assert "benchmarks" in result
        assert "json_serialize_10k_ms" in result["benchmarks"]

    def test_unknown_command(self):
        from windows_ai.cli.commands import CLIRunner
        cli = CLIRunner()
        result = cli.run(["nonexistent_cmd"])
        assert result["status"] == "error"

    def test_empty_args_shows_help(self):
        from windows_ai.cli.commands import CLIRunner
        cli = CLIRunner()
        result = cli.run([])
        assert result["status"] == "success"
        assert "commands" in result

    def test_register_custom_command(self):
        from windows_ai.cli.commands import CLIRunner
        cli = CLIRunner()
        cli.register("custom:test", lambda args: {"status": "success", "data": args}, "Custom test")
        result = cli.run(["custom:test", "arg1"])
        assert result["data"] == ["arg1"]

    def test_plugins_list(self):
        from windows_ai.cli.commands import CLIRunner
        cli = CLIRunner()
        result = cli.run(["plugins:list"])
        assert result["status"] in ("success", "error")

    def test_config_get_missing_key(self):
        from windows_ai.cli.commands import CLIRunner
        cli = CLIRunner()
        result = cli.run(["config:get"])
        assert result["status"] == "error"

    def test_config_set_missing_args(self):
        from windows_ai.cli.commands import CLIRunner
        cli = CLIRunner()
        result = cli.run(["config:set"])
        assert result["status"] == "error"

    def test_mesh_status(self):
        from windows_ai.cli.commands import CLIRunner
        cli = CLIRunner()
        result = cli.run(["mesh:status"])
        assert result["status"] == "success"

    def test_mesh_peers(self):
        from windows_ai.cli.commands import CLIRunner
        cli = CLIRunner()
        result = cli.run(["mesh:peers"])
        assert result["status"] == "success"

    def test_agents_list(self):
        from windows_ai.cli.commands import CLIRunner
        cli = CLIRunner()
        result = cli.run(["agents:list"])
        assert result["status"] in ("success", "error")

    def test_get_commands(self):
        from windows_ai.cli.commands import CLIRunner
        cli = CLIRunner()
        cmds = cli.get_commands()
        assert len(cmds) >= 10
        assert "status" in cmds
        assert "health" in cmds


# ========================================================================
# Expanded Agent Coordinator
# ========================================================================

class TestAgentCoordinator:
    """Tests for expanded mesh agent coordinator."""

    def test_init_without_mesh(self):
        from windows_ai.mesh.agent_coordinator import AgentCoordinator
        coord = AgentCoordinator()
        assert len(coord.capabilities) >= 5

    def test_distribute_inference_local(self):
        from windows_ai.mesh.agent_coordinator import AgentCoordinator
        coord = AgentCoordinator()
        result = coord.distribute_inference("gpt-4", "Hello world")
        assert result["status"] == "success"

    def test_distribute_rag_search(self):
        from windows_ai.mesh.agent_coordinator import AgentCoordinator
        coord = AgentCoordinator()
        result = coord.distribute_rag_search("test query", top_k=3)
        assert result["status"] == "success"

    def test_execute_pipeline(self):
        from windows_ai.mesh.agent_coordinator import AgentCoordinator
        coord = AgentCoordinator()
        steps = [
            {"task_type": "ai_inference", "payload": {"prompt": "step 1"}},
            {"task_type": "ai_inference", "payload": {"prompt": "step 2"}},
        ]
        result = coord.execute_pipeline("test-pipeline", steps)
        assert result["status"] == "success"
        assert result["steps_completed"] == 2

    def test_register_capability(self):
        from windows_ai.mesh.agent_coordinator import AgentCoordinator
        coord = AgentCoordinator()
        coord.register_capability("custom_capability", models=["model-a"])
        assert "custom_capability" in coord.capabilities

    def test_get_mesh_capabilities(self):
        from windows_ai.mesh.agent_coordinator import AgentCoordinator
        coord = AgentCoordinator()
        result = coord.get_mesh_capabilities()
        assert result["status"] == "success"
        assert "ai_inference" in result["capabilities"]

    def test_stats(self):
        from windows_ai.mesh.agent_coordinator import AgentCoordinator
        coord = AgentCoordinator()
        stats = coord.stats()
        assert stats["status"] == "success"
        assert stats["capabilities"] >= 5

    def test_broadcast_capability(self):
        from windows_ai.mesh.agent_coordinator import AgentCoordinator
        coord = AgentCoordinator()
        coord.broadcast_capability("embeddings", False)
        assert coord.capabilities["embeddings"].available is False

    def test_get_pending_requests(self):
        from windows_ai.mesh.agent_coordinator import AgentCoordinator
        coord = AgentCoordinator()
        pending = coord.get_pending_requests()
        assert isinstance(pending, list)


# ========================================================================
# Mesh Node (unit-level)
# ========================================================================

class TestMeshNodeUnit:
    """Unit tests for MeshNode without network."""

    def test_node_creation(self):
        from windows_ai.mesh.mesh_node import MeshNode
        node = MeshNode(node_id="test-node", port=19999)
        assert node.node_id == "test-node"
        assert node.port == 19999

    def test_node_status(self):
        from windows_ai.mesh.mesh_node import MeshNode
        node = MeshNode(node_id="test-node")
        status = node.get_status()
        assert status["status"] == "success"
        assert status["node_id"] == "test-node"
        assert status["role"] == "follower"

    def test_add_peer(self):
        from windows_ai.mesh.mesh_node import MeshNode
        node = MeshNode(node_id="test-node")
        result = node.add_peer("peer-1", "127.0.0.1", 8888, ["ai_inference"])
        assert result["status"] == "success"
        assert "peer-1" in node.peers

    def test_register_handler(self):
        from windows_ai.mesh.mesh_node import MeshNode
        node = MeshNode(node_id="test-node")
        node.register_handler("custom", lambda msg: {"status": "ok"})
        assert "custom" in node.message_handlers


# ========================================================================
# State Sync (unit-level)
# ========================================================================

class TestStateSyncUnit:
    """Unit tests for state synchronization."""

    def test_set_and_get(self):
        from windows_ai.mesh.mesh_node import MeshNode
        from windows_ai.mesh.state_sync import StateSync
        node = MeshNode(node_id="test-node")
        sync = StateSync(node)
        sync.set("key1", "value1")
        result = sync.get("key1")
        assert result["status"] == "success"
        assert result["value"] == "value1"

    def test_get_missing_key(self):
        from windows_ai.mesh.mesh_node import MeshNode
        from windows_ai.mesh.state_sync import StateSync
        node = MeshNode(node_id="test-node")
        sync = StateSync(node)
        result = sync.get("nonexistent")
        assert result["status"] == "error"

    def test_delete_key(self):
        from windows_ai.mesh.mesh_node import MeshNode
        from windows_ai.mesh.state_sync import StateSync
        node = MeshNode(node_id="test-node")
        sync = StateSync(node)
        sync.set("key1", "value1")
        result = sync.delete("key1")
        assert result["status"] == "success"

    def test_get_all(self):
        from windows_ai.mesh.mesh_node import MeshNode
        from windows_ai.mesh.state_sync import StateSync
        node = MeshNode(node_id="test-node")
        sync = StateSync(node)
        sync.set("a", 1)
        sync.set("b", 2)
        result = sync.get_all()
        assert result["status"] == "success"
        assert len(result["state"]) == 2

    def test_status(self):
        from windows_ai.mesh.mesh_node import MeshNode
        from windows_ai.mesh.state_sync import StateSync
        node = MeshNode(node_id="test-node")
        sync = StateSync(node)
        sync.set("x", 42)
        status = sync.get_status()
        assert status["state_keys"] == 1


# ========================================================================
# Task Queue (unit-level)
# ========================================================================

class TestTaskQueueUnit:
    """Unit tests for distributed task queue."""

    def test_submit_and_get_task(self):
        from windows_ai.mesh.mesh_node import MeshNode
        from windows_ai.mesh.task_queue import DistributedTaskQueue
        node = MeshNode(node_id="test-node")
        queue = DistributedTaskQueue(node)
        result = queue.submit_task("test_type", {"data": "hello"})
        assert result["status"] == "success"
        assert "task_id" in result

    def test_register_handler(self):
        from windows_ai.mesh.mesh_node import MeshNode
        from windows_ai.mesh.task_queue import DistributedTaskQueue
        node = MeshNode(node_id="test-node")
        queue = DistributedTaskQueue(node)
        queue.register_handler("custom", lambda p: {"ok": True})
        assert "custom" in queue.task_handlers

    def test_queue_status(self):
        from windows_ai.mesh.mesh_node import MeshNode
        from windows_ai.mesh.task_queue import DistributedTaskQueue
        node = MeshNode(node_id="test-node")
        queue = DistributedTaskQueue(node)
        status = queue.get_queue_status()
        assert status["status"] == "success"
        assert "total_tasks" in status

    def test_get_task_not_found(self):
        from windows_ai.mesh.mesh_node import MeshNode
        from windows_ai.mesh.task_queue import DistributedTaskQueue
        node = MeshNode(node_id="test-node")
        queue = DistributedTaskQueue(node)
        result = queue.get_task_status("nonexistent-id")
        assert result["status"] == "error"


# ========================================================================
# Sandbox Security
# ========================================================================

class TestSandboxSecurity:
    """Tests for sandbox manager."""

    @pytest.mark.asyncio
    async def test_initialize_default(self):
        from windows_ai.security.sandbox import SandboxManager
        sm = SandboxManager()
        await sm.initialize()
        assert sm._initialized is True

    @pytest.mark.asyncio
    async def test_set_level(self):
        from windows_ai.security.sandbox import SandboxManager, SandboxLevel
        sm = SandboxManager()
        await sm.initialize()
        sm.set_level(SandboxLevel.STRICT)
        assert sm.config.level == SandboxLevel.STRICT
        assert sm.config.allow_file_write is False

    def test_path_allowed(self):
        from windows_ai.security.sandbox import SandboxManager
        sm = SandboxManager()
        assert sm.is_path_allowed("/tmp/test") is True

    def test_path_blocked(self):
        from windows_ai.security.sandbox import SandboxManager, SandboxLevel
        sm = SandboxManager()
        sm.set_level(SandboxLevel.STANDARD)
        assert sm.is_path_allowed("/etc/passwd") is False

    def test_command_blocked(self):
        from windows_ai.security.sandbox import SandboxManager, SandboxLevel
        sm = SandboxManager()
        sm.set_level(SandboxLevel.STANDARD)
        assert sm.is_command_allowed("rm -rf /") is False
        assert sm.is_command_allowed("ls /tmp") is True

    def test_get_config(self):
        from windows_ai.security.sandbox import SandboxManager
        sm = SandboxManager()
        config = sm.get_config()
        assert "level" in config
        assert "network_access" in config

    @pytest.mark.asyncio
    async def test_file_read(self):
        from windows_ai.security.sandbox import SandboxManager
        sm = SandboxManager()
        await sm.initialize()
        # Write a temp file, then read through sandbox
        with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as f:
            f.write("sandbox test")
            path = f.name
        try:
            result = await sm.execute_file_operation("read", path)
            assert result["success"] is True
            assert result["data"] == "sandbox test"
        finally:
            os.unlink(path)

    @pytest.mark.asyncio
    async def test_file_write_blocked_in_strict(self):
        from windows_ai.security.sandbox import SandboxManager, SandboxLevel
        sm = SandboxManager()
        await sm.initialize({"level": "strict"})
        with pytest.raises(PermissionError):
            await sm.execute_file_operation("write", "/tmp/sandbox_test.txt", "data")


# ========================================================================
# Module Imports
# ========================================================================

class TestModuleImports:
    """Verify all new modules import correctly."""

    def test_observability_module(self):
        from windows_ai.observability import Tracer, MetricsCollector, StructuredLogger
        assert Tracer is not None
        assert MetricsCollector is not None
        assert StructuredLogger is not None

    def test_observability_span(self):
        from windows_ai.observability import Span, SpanContext
        assert Span is not None

    def test_observability_metrics(self):
        from windows_ai.observability import Counter, Histogram, Gauge
        assert Counter is not None

    def test_cli_module(self):
        from windows_ai.cli import CLIRunner
        assert CLIRunner is not None

    def test_mesh_agent_coordinator(self):
        from windows_ai.mesh import AgentCoordinator
        assert AgentCoordinator is not None
