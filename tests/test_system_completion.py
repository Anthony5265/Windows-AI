"""
Tests for expanded terminal engine, snapshot module, backup/rollback,
monitoring dashboard, frameworks, and broader system integration.
"""
import pytest
import asyncio
import os
import tempfile
import json
from pathlib import Path
from unittest.mock import MagicMock, patch


# ========================================================================
# Terminal Engine (expanded)
# ========================================================================

class TestTerminalEngine:
    """Test the expanded terminal engine."""

    def test_basic_run(self):
        from windows_ai.terminal.engine import TerminalEngine
        engine = TerminalEngine()
        result = engine.run("echo hello")
        assert result.success
        assert result.stdout == "hello"

    def test_command_result_properties(self):
        from windows_ai.terminal.engine import TerminalEngine
        engine = TerminalEngine()
        result = engine.run("echo test")
        assert result.return_code == 0
        assert result.duration_ms >= 0
        assert result.command == "echo test"
        assert result.session_id == "default"

    def test_blocked_pipe(self):
        from windows_ai.terminal.engine import TerminalEngine
        engine = TerminalEngine()
        with pytest.raises(ValueError, match="Blocked"):
            engine.run("echo hello | cat")

    def test_blocked_redirect(self):
        from windows_ai.terminal.engine import TerminalEngine
        engine = TerminalEngine()
        with pytest.raises(ValueError, match="Blocked"):
            engine.run("echo hello > /tmp/test")

    def test_blocked_dangerous_command(self):
        from windows_ai.terminal.engine import TerminalEngine
        engine = TerminalEngine()
        with pytest.raises(ValueError, match="Blocked"):
            engine.run("rm -rf /")

    def test_session_management(self):
        from windows_ai.terminal.engine import TerminalEngine
        engine = TerminalEngine()
        session = engine.create_session(session_id="test-session")
        assert session.session_id == "test-session"
        assert engine.get_session("test-session") is not None

    def test_close_session(self):
        from windows_ai.terminal.engine import TerminalEngine
        engine = TerminalEngine()
        engine.create_session(session_id="temp")
        assert engine.close_session("temp") is True
        assert engine.get_session("temp") is None

    def test_cannot_close_default(self):
        from windows_ai.terminal.engine import TerminalEngine
        engine = TerminalEngine()
        assert engine.close_session("default") is False

    def test_list_sessions(self):
        from windows_ai.terminal.engine import TerminalEngine
        engine = TerminalEngine()
        engine.create_session(session_id="s1")
        sessions = engine.list_sessions()
        ids = [s["session_id"] for s in sessions]
        assert "default" in ids
        assert "s1" in ids

    def test_run_in_session(self):
        from windows_ai.terminal.engine import TerminalEngine
        engine = TerminalEngine()
        session = engine.create_session(session_id="my-session")
        result = engine.run("echo session", session_id="my-session")
        assert result.stdout == "session"
        assert result.session_id == "my-session"

    def test_history(self):
        from windows_ai.terminal.engine import TerminalEngine
        engine = TerminalEngine()
        engine.run("echo one")
        engine.run("echo two")
        history = engine.get_history(limit=10)
        assert len(history) == 2

    def test_session_history(self):
        from windows_ai.terminal.engine import TerminalEngine
        engine = TerminalEngine()
        engine.create_session(session_id="s1")
        engine.run("echo a", session_id="s1")
        engine.run("echo b", session_id="default")
        h = engine.get_history(session_id="s1")
        assert len(h) == 1

    def test_search_history(self):
        from windows_ai.terminal.engine import TerminalEngine
        engine = TerminalEngine()
        engine.run("echo hello")
        engine.run("echo world")
        results = engine.search_history("hello")
        assert len(results) == 1

    def test_clear_history(self):
        from windows_ai.terminal.engine import TerminalEngine
        engine = TerminalEngine()
        engine.run("echo x")
        count = engine.clear_history()
        assert count >= 1
        assert engine.get_history() == []

    def test_timeout(self):
        from windows_ai.terminal.engine import TerminalEngine
        engine = TerminalEngine()
        result = engine.run("sleep 10", timeout=0.1)
        assert result.return_code == -1
        assert "timed out" in result.stderr

    @pytest.mark.asyncio
    async def test_async_run(self):
        from windows_ai.terminal.engine import TerminalEngine
        engine = TerminalEngine()
        result = await engine.run_async("echo async")
        assert result.success
        assert result.stdout == "async"

    @pytest.mark.asyncio
    async def test_async_timeout(self):
        from windows_ai.terminal.engine import TerminalEngine
        engine = TerminalEngine()
        result = await engine.run_async("sleep 10", timeout=0.1)
        assert result.return_code == -1

    def test_stats(self):
        from windows_ai.terminal.engine import TerminalEngine
        engine = TerminalEngine()
        engine.run("echo stat")
        stats = engine.stats()
        assert stats["sessions"] >= 1
        assert stats["global_history"] >= 1

    def test_command_result_to_dict(self):
        from windows_ai.terminal.engine import TerminalEngine
        engine = TerminalEngine()
        result = engine.run("echo dict")
        d = result.to_dict()
        assert isinstance(d, dict)
        assert d["command"] == "echo dict"

    def test_terminal_import(self):
        from windows_ai.terminal import TerminalEngine, TerminalSession, CommandResult
        assert TerminalEngine is not None
        assert TerminalSession is not None
        assert CommandResult is not None


# ========================================================================
# Snapshot Module
# ========================================================================

class TestSnapshotModule:
    """Test configuration snapshot utilities."""

    def test_capture_and_rollback(self):
        from windows_ai.snapshot import capture, rollback, remove, SNAPSHOT_DIR

        with tempfile.TemporaryDirectory() as tmpdir:
            # Create a test file
            test_file = Path(tmpdir) / "config.json"
            test_file.write_text('{"version": 1}')

            # Capture snapshot
            dest = capture("test_feature", test_file)
            assert dest.exists()

            # Modify original
            test_file.write_text('{"version": 2}')

            # Rollback
            rollback("test_feature")
            assert json.loads(test_file.read_text())["version"] == 1

            # Cleanup
            remove("test_feature")

    def test_capture_directory(self):
        from windows_ai.snapshot import capture, remove

        with tempfile.TemporaryDirectory() as tmpdir:
            src = Path(tmpdir) / "src_dir"
            src.mkdir()
            (src / "file.txt").write_text("data")

            dest = capture("dir_feature", src)
            assert dest.exists()

            remove("dir_feature")

    def test_remove_nonexistent(self):
        from windows_ai.snapshot import remove
        # Should not raise
        remove("nonexistent_feature_xyz")


# ========================================================================
# Backup Recovery
# ========================================================================

class TestBackupRecovery:
    """Test backup and recovery system."""

    def test_import(self):
        from windows_ai.backup.backup_recovery import BackupStatus, BackupFrequency
        assert BackupStatus is not None
        assert BackupFrequency is not None

    def test_backup_status_enum(self):
        from windows_ai.backup.backup_recovery import BackupStatus
        assert hasattr(BackupStatus, "COMPLETED")
        assert hasattr(BackupStatus, "FAILED")


# ========================================================================
# Rollback Module
# ========================================================================

class TestRollbackModule:
    """Test rollback system."""

    def test_import_engine(self):
        from windows_ai.rollback.rollback_engine import RollbackEngine, RollbackStatus
        assert RollbackEngine is not None
        assert RollbackStatus is not None

    def test_import_snapshot_manager(self):
        from windows_ai.rollback.snapshot_manager import SnapshotManager
        assert SnapshotManager is not None

    def test_import_version_history(self):
        from windows_ai.rollback.version_history import VersionHistory
        assert VersionHistory is not None


# ========================================================================
# Monitoring Dashboard
# ========================================================================

class TestMonitoringDashboard:
    """Test monitoring dashboard."""

    def test_import(self):
        from windows_ai.monitoring.dashboard import MonitoringDashboard, AlertSeverity
        assert MonitoringDashboard is not None
        assert AlertSeverity is not None

    def test_create_dashboard(self):
        from windows_ai.monitoring.dashboard import MonitoringDashboard
        dashboard = MonitoringDashboard()
        assert dashboard is not None

    def test_alert_severity(self):
        from windows_ai.monitoring.dashboard import AlertSeverity
        assert AlertSeverity.INFO is not None
        assert AlertSeverity.WARNING is not None
        assert AlertSeverity.CRITICAL is not None

    def test_dashboard_factory(self):
        from windows_ai.monitoring.dashboard import DashboardFactory
        assert DashboardFactory is not None


# ========================================================================
# Metrics Module
# ========================================================================

class TestMetricsModule:
    """Test metrics collection module."""

    def test_import_plugin_metrics(self):
        from windows_ai.metrics.plugin_metrics import PluginPerformanceMonitor
        assert PluginPerformanceMonitor is not None

    def test_import_real_time(self):
        from windows_ai.metrics.real_time_metrics import MetricsCollector as RTMetrics
        assert RTMetrics is not None

    def test_plugin_metrics_creation(self):
        from windows_ai.metrics.plugin_metrics import PluginPerformanceMonitor
        monitor = PluginPerformanceMonitor()
        assert monitor is not None


# ========================================================================
# Framework Integrations
# ========================================================================

class TestFrameworkIntegrations:
    """Test AI framework integrations."""

    def test_unified_llm(self):
        from windows_ai.frameworks.unified_llm import UnifiedLLMProvider
        assert UnifiedLLMProvider is not None

    def test_mcp_integration(self):
        from windows_ai.frameworks.mcp_integration import MCPServer
        assert MCPServer is not None

    def test_ollama_integration(self):
        from windows_ai.frameworks.ollama_integration import OllamaManager
        assert OllamaManager is not None

    def test_langchain_integration(self):
        from windows_ai.frameworks.langchain_integration import LangChainManager
        assert LangChainManager is not None


# ========================================================================
# Cloud Sync Module
# ========================================================================

class TestCloudSyncModule:
    """Test cloud sync comprehensive."""

    def test_import_protocol(self):
        from windows_ai.cloud_sync.protocol import SyncProtocol
        assert SyncProtocol is not None

    def test_import_client(self):
        from windows_ai.cloud_sync.client import SyncClient
        assert SyncClient is not None

    def test_import_models(self):
        from windows_ai.cloud_sync.models import DataCategory, SyncState
        assert DataCategory is not None
        assert SyncState is not None


# ========================================================================
# System Modules
# ========================================================================

class TestSystemModules:
    """Test system-level modules."""

    def test_process_monitor(self):
        from windows_ai.system.process_monitor import ProcessMonitor
        monitor = ProcessMonitor()
        assert monitor is not None


# ========================================================================
# Core Modules Deep
# ========================================================================

class TestCoreModulesDeep:
    """Deep tests for core module functionality."""

    def test_credential_manager(self):
        from windows_ai.core.credential_manager import CredentialManager
        cm = CredentialManager()
        assert cm is not None

    def test_error_handling(self):
        from windows_ai.core.error_handling import ErrorHandler
        assert ErrorHandler is not None

    @pytest.mark.asyncio
    async def test_cache(self):
        from windows_ai.core.cache import InMemoryCache
        cache = InMemoryCache()
        await cache.set("key", "value", ttl=60)
        assert await cache.get("key") == "value"
        await cache.delete("key")
        assert await cache.get("key") is None

    @pytest.mark.asyncio
    async def test_cache_stats(self):
        from windows_ai.core.cache import InMemoryCache
        cache = InMemoryCache()
        await cache.set("a", 1)
        await cache.get("a")
        await cache.get("nonexistent")
        stats = await cache.get_stats()
        assert stats["hits"] >= 1
        assert stats["misses"] >= 1

    def test_circuit_breaker(self):
        from windows_ai.core.circuit_breaker import CircuitBreaker
        cb = CircuitBreaker("test-service")
        assert cb.state.value == "closed"
        stats = cb.stats()
        assert stats["state"] == "closed"

    def test_provider_failover(self):
        from windows_ai.core.provider_failover import ProviderFailover
        pf = ProviderFailover()
        assert pf is not None

    def test_lazy_loader(self):
        from windows_ai.core.lazy_loader import LazyManagerLoader
        loader = LazyManagerLoader()
        assert loader is not None

    def test_crash_recovery(self):
        from windows_ai.core.crash_recovery import CrashRecoveryManager
        crm = CrashRecoveryManager()
        assert crm is not None


# ========================================================================
# Search Module
# ========================================================================

class TestSearchModuleDeep:
    """Deep tests for search module."""

    def test_plugin_search(self):
        from windows_ai.search.plugin_search import PluginSearchIndex
        idx = PluginSearchIndex()
        assert idx is not None

    def test_search_index_add_and_query(self):
        from windows_ai.search.plugin_search import PluginSearchIndex
        idx = PluginSearchIndex()
        idx.index_plugin({"id": "p1", "name": "Audio Transcription", "description": "transcription using whisper model"})
        idx.index_plugin({"id": "p2", "name": "Image Classification", "description": "image classification"})
        results = idx.search("audio transcription", top_k=5)
        assert len(results) >= 1


# ========================================================================
# RAG Module Deep
# ========================================================================

class TestRAGModuleDeep:
    """Deep tests for RAG pipeline."""

    def test_imports(self):
        from windows_ai.rag import HybridSearch, BM25Index
        assert HybridSearch is not None
        assert BM25Index is not None

    def test_bm25_index(self):
        from windows_ai.rag.hybrid_search import BM25Index
        idx = BM25Index()
        idx.add_document("d1", "The quick brown fox jumps over the lazy dog")
        idx.add_document("d2", "A fast red car drives on the highway")
        results = idx.search("quick fox", top_k=2)
        assert len(results) >= 1


# ========================================================================
# Integration: Observability + API
# ========================================================================

class TestObservabilityIntegration:
    """Test observability module used through API and directly."""

    def test_tracer_with_metrics(self):
        from windows_ai.observability.tracing import Tracer
        from windows_ai.observability.metrics import MetricsCollector

        tracer = Tracer(service_name="test")
        metrics = MetricsCollector()
        latency_hist = metrics.histogram("test_latency")

        with tracer.start_span("test_op") as span:
            span.set_attribute("test", True)

        latency_hist.observe(span.duration_ms)
        assert latency_hist.count == 1

    def test_structured_logging_with_tracer(self):
        from windows_ai.observability.tracing import Tracer
        from windows_ai.observability.structured_logging import StructuredLogger

        tracer = Tracer()
        slog = StructuredLogger(output="none")

        with tracer.start_span("logged_op") as span:
            with slog.context(trace_id=span.context.trace_id):
                entry = slog.info("Operation complete", status="ok")
                assert entry.get("trace_id") == span.context.trace_id
