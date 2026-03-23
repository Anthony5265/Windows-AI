"""Tests for community plugin submission, CVE monitoring, and additional coverage."""
import pytest


# ========================================================================
# Plugin Submission Process
# ========================================================================

class TestPluginSubmission:
    """Test community plugin submission workflow."""

    def test_import(self):
        from windows_ai.plugins.submission import PluginSubmissionManager
        assert PluginSubmissionManager is not None

    def test_status_enum(self):
        from windows_ai.plugins.submission import SubmissionStatus
        assert SubmissionStatus.DRAFT.value == "draft"
        assert SubmissionStatus.PUBLISHED.value == "published"

    def test_rejection_reasons(self):
        from windows_ai.plugins.submission import RejectionReason
        assert RejectionReason.SECURITY_ISSUE.value == "security_issue"
        assert RejectionReason.MALICIOUS_CODE.value == "malicious_code"

    def test_create_submission(self):
        from windows_ai.plugins.submission import PluginSubmissionManager
        mgr = PluginSubmissionManager()
        sub = mgr.create_submission(
            plugin_id="my-plugin", plugin_name="My Plugin",
            author="dev@test.com", version="1.0.0",
            description="A test plugin for testing"
        )
        assert sub.submission_id == "sub-0001"
        assert sub.status.value == "draft"

    def test_submit(self):
        from windows_ai.plugins.submission import PluginSubmissionManager
        mgr = PluginSubmissionManager()
        sub = mgr.create_submission("p1", "Plugin 1", "author", "1.0.0", "Test plugin desc")
        result = mgr.submit(sub.submission_id)
        assert result["status"] == "success"
        assert sub.status.value == "submitted"

    def test_validate_success(self):
        from windows_ai.plugins.submission import PluginSubmissionManager
        mgr = PluginSubmissionManager()
        sub = mgr.create_submission("p1", "Plugin 1", "author", "1.0.0", "A valid description")
        mgr.submit(sub.submission_id)
        result = mgr.validate(sub.submission_id)
        assert result["passed"] is True
        assert sub.status.value == "security_review"

    def test_validate_failure(self):
        from windows_ai.plugins.submission import PluginSubmissionManager
        mgr = PluginSubmissionManager()
        sub = mgr.create_submission("p1", "Plugin 1", "author", "1.0.0", "short")
        mgr.submit(sub.submission_id)
        result = mgr.validate(sub.submission_id)
        assert result["passed"] is False

    def test_security_review(self):
        from windows_ai.plugins.submission import PluginSubmissionManager
        mgr = PluginSubmissionManager()
        sub = mgr.create_submission("p1", "Plugin 1", "author", "1.0.0", "A valid description")
        mgr.submit(sub.submission_id)
        mgr.validate(sub.submission_id)
        result = mgr.security_review(sub.submission_id)
        assert result["passed"] is True
        assert sub.status.value == "community_review"

    def test_approve(self):
        from windows_ai.plugins.submission import PluginSubmissionManager
        mgr = PluginSubmissionManager()
        sub = mgr.create_submission("p1", "Plugin 1", "author", "1.0.0", "A valid description")
        mgr.submit(sub.submission_id)
        mgr.validate(sub.submission_id)
        mgr.security_review(sub.submission_id)
        result = mgr.approve(sub.submission_id, reviewer="admin")
        assert result["status"] == "success"
        assert sub.status.value == "approved"

    def test_publish(self):
        from windows_ai.plugins.submission import PluginSubmissionManager
        mgr = PluginSubmissionManager()
        sub = mgr.create_submission("p1", "Plugin 1", "author", "1.0.0", "A valid description")
        mgr.submit(sub.submission_id)
        mgr.validate(sub.submission_id)
        mgr.security_review(sub.submission_id)
        mgr.approve(sub.submission_id, reviewer="admin")
        result = mgr.publish(sub.submission_id)
        assert result["status"] == "success"
        assert sub.status.value == "published"

    def test_reject(self):
        from windows_ai.plugins.submission import PluginSubmissionManager, RejectionReason
        mgr = PluginSubmissionManager()
        sub = mgr.create_submission("p1", "Plugin 1", "author", "1.0.0", "A valid description")
        result = mgr.reject(sub.submission_id, RejectionReason.LOW_QUALITY, "Needs improvement")
        assert result["status"] == "success"
        assert sub.status.value == "rejected"

    def test_list_submissions(self):
        from windows_ai.plugins.submission import PluginSubmissionManager
        mgr = PluginSubmissionManager()
        mgr.create_submission("p1", "Plugin 1", "a1", "1.0.0", "Description one")
        mgr.create_submission("p2", "Plugin 2", "a2", "1.0.0", "Description two")
        subs = mgr.list_submissions()
        assert len(subs) == 2

    def test_list_by_status(self):
        from windows_ai.plugins.submission import PluginSubmissionManager, SubmissionStatus
        mgr = PluginSubmissionManager()
        mgr.create_submission("p1", "P1", "a", "1.0.0", "Desc one")
        sub2 = mgr.create_submission("p2", "P2", "a", "1.0.0", "Desc two")
        mgr.submit(sub2.submission_id)
        subs = mgr.list_submissions(status=SubmissionStatus.SUBMITTED)
        assert len(subs) == 1

    def test_list_by_author(self):
        from windows_ai.plugins.submission import PluginSubmissionManager
        mgr = PluginSubmissionManager()
        mgr.create_submission("p1", "P1", "alice", "1.0.0", "Desc one")
        mgr.create_submission("p2", "P2", "bob", "1.0.0", "Desc two")
        subs = mgr.list_submissions(author="alice")
        assert len(subs) == 1

    def test_add_comment(self):
        from windows_ai.plugins.submission import PluginSubmissionManager
        mgr = PluginSubmissionManager()
        sub = mgr.create_submission("p1", "P1", "a", "1.0.0", "Desc")
        result = mgr.add_comment(sub.submission_id, "reviewer1", "Looks good!")
        assert result["status"] == "success"
        assert len(sub.review_comments) == 1

    def test_get_stats(self):
        from windows_ai.plugins.submission import PluginSubmissionManager
        mgr = PluginSubmissionManager()
        mgr.create_submission("p1", "P1", "a", "1.0.0", "Desc")
        stats = mgr.get_stats()
        assert stats["total"] == 1
        assert stats["draft"] == 1

    def test_version_validation(self):
        from windows_ai.plugins.submission import PluginSubmissionManager
        assert PluginSubmissionManager._validate_version("1.0.0") is True
        assert PluginSubmissionManager._validate_version("2.1") is True
        assert PluginSubmissionManager._validate_version("1.0.0-beta") is True
        assert PluginSubmissionManager._validate_version("invalid") is False

    def test_custom_validator(self):
        from windows_ai.plugins.submission import PluginSubmissionManager
        mgr = PluginSubmissionManager()
        mgr.add_validator(lambda sub: {"custom_check": True})
        sub = mgr.create_submission("p1", "P1", "a", "1.0.0", "Valid description here")
        mgr.submit(sub.submission_id)
        result = mgr.validate(sub.submission_id)
        assert "custom_check" in result["validation"]

    def test_get_submission(self):
        from windows_ai.plugins.submission import PluginSubmissionManager
        mgr = PluginSubmissionManager()
        sub = mgr.create_submission("p1", "P1", "a", "1.0.0", "Desc")
        info = mgr.get_submission(sub.submission_id)
        assert info is not None
        assert info["plugin_id"] == "p1"

    def test_get_nonexistent(self):
        from windows_ai.plugins.submission import PluginSubmissionManager
        mgr = PluginSubmissionManager()
        assert mgr.get_submission("nonexistent") is None

    def test_full_workflow(self):
        """Test complete submission → publish workflow."""
        from windows_ai.plugins.submission import PluginSubmissionManager
        mgr = PluginSubmissionManager()

        # Create and submit
        sub = mgr.create_submission(
            "awesome-plugin", "Awesome Plugin",
            "developer@example.com", "1.0.0",
            "An awesome plugin that does amazing things"
        )
        mgr.submit(sub.submission_id)

        # Validate
        val = mgr.validate(sub.submission_id)
        assert val["passed"] is True

        # Security review
        sec = mgr.security_review(sub.submission_id)
        assert sec["passed"] is True

        # Approve and publish
        mgr.approve(sub.submission_id, reviewer="admin@example.com")
        result = mgr.publish(sub.submission_id)
        assert result["status"] == "success"

        # Verify final state
        info = mgr.get_submission(sub.submission_id)
        assert info["status"] == "published"


# ========================================================================
# Additional module coverage
# ========================================================================

class TestObservabilityModules:
    """Test observability module."""

    def test_tracing_import(self):
        from windows_ai.observability.tracing import Tracer
        assert Tracer is not None

    def test_metrics_import(self):
        from windows_ai.observability.metrics import MetricsCollector
        assert MetricsCollector is not None

    def test_structured_logging_import(self):
        from windows_ai.observability.structured_logging import StructuredLogger
        assert StructuredLogger is not None

    def test_create_tracer(self):
        from windows_ai.observability.tracing import Tracer
        tracer = Tracer(service_name="test-service")
        assert tracer is not None

    def test_create_metrics(self):
        from windows_ai.observability.metrics import MetricsCollector
        mc = MetricsCollector()
        assert mc is not None

    def test_create_logger(self):
        from windows_ai.observability.structured_logging import StructuredLogger
        sl = StructuredLogger()
        assert sl is not None


class TestMeshModules:
    """Test mesh networking modules."""

    def test_mesh_node_import(self):
        from windows_ai.mesh.mesh_node import MeshNode
        assert MeshNode is not None

    def test_peer_discovery_import(self):
        from windows_ai.mesh.peer_discovery import PeerDiscovery
        assert PeerDiscovery is not None

    def test_state_sync_import(self):
        from windows_ai.mesh.state_sync import StateSync
        assert StateSync is not None

    def test_task_queue_import(self):
        from windows_ai.mesh.task_queue import DistributedTaskQueue
        assert DistributedTaskQueue is not None

    def test_agent_coordinator_import(self):
        from windows_ai.mesh.agent_coordinator import AgentCoordinator
        assert AgentCoordinator is not None


class TestCLIModule:
    """Test CLI module."""

    def test_cli_import(self):
        from windows_ai.cli.commands import CLIRunner
        assert CLIRunner is not None


class TestRAGModules:
    """Test RAG pipeline modules."""

    def test_rag_engine_import(self):
        from windows_ai.rag.engine import RAGEngine
        assert RAGEngine is not None

    def test_document_processor_import(self):
        from windows_ai.rag.document_processor import RAGDocumentProcessor
        assert RAGDocumentProcessor is not None

    def test_hybrid_search_import(self):
        from windows_ai.rag.hybrid_search import HybridSearch
        assert HybridSearch is not None

    def test_file_indexer_import(self):
        from windows_ai.rag.file_indexer import FileSystemIndexer
        assert FileSystemIndexer is not None


class TestCacheModule:
    """Test cache infrastructure."""

    def test_cache_import(self):
        from windows_ai.core.cache import InMemoryCache
        assert InMemoryCache is not None

    @pytest.mark.asyncio
    async def test_cache_operations(self):
        from windows_ai.core.cache import InMemoryCache
        cache = InMemoryCache()
        await cache.set("key1", "value1")
        assert await cache.get("key1") == "value1"
        assert await cache.get("nonexistent") is None

    @pytest.mark.asyncio
    async def test_cache_delete(self):
        from windows_ai.core.cache import InMemoryCache
        cache = InMemoryCache()
        await cache.set("k", "v")
        await cache.delete("k")
        assert await cache.get("k") is None

    @pytest.mark.asyncio
    async def test_cache_clear(self):
        from windows_ai.core.cache import InMemoryCache
        cache = InMemoryCache()
        await cache.set("a", 1)
        await cache.set("b", 2)
        await cache.clear()
        assert await cache.get("a") is None


class TestCircuitBreakerModule:
    """Test circuit breaker module."""

    def test_registry_import(self):
        from windows_ai.core.circuit_breaker import CircuitBreakerRegistry
        assert CircuitBreakerRegistry is not None

    def test_create_breaker(self):
        from windows_ai.core.circuit_breaker import CircuitBreaker
        cb = CircuitBreaker(name="test", failure_threshold=3, recovery_timeout=30)
        assert cb is not None
        assert cb.name == "test"
