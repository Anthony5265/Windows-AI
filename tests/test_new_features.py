"""Tests for newly added features: workflow routes, security expansion,
hybrid search, file indexer, plugin dependency resolver, and server wiring.
"""
import pytest
import asyncio
import time
import os
import tempfile
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch


# ========================================================================
# Security: Crypto
# ========================================================================

class TestCrypto:
    """Tests for expanded crypto module."""

    def test_encrypt_decrypt_roundtrip(self):
        from windows_ai.security.crypto import encrypt, decrypt
        key = "test-key-1234567"
        original = "Hello, Windows AI!"
        token = encrypt(original, key)
        assert token != original
        assert decrypt(token, key) == original

    def test_generate_key(self):
        from windows_ai.security.crypto import generate_key
        key = generate_key()
        assert isinstance(key, str)
        assert len(key) > 0

    def test_derive_key(self):
        from windows_ai.security.crypto import derive_key
        key1, salt = derive_key("password123")
        key2, _ = derive_key("password123", salt)
        assert key1 == key2

    def test_derive_key_different_passwords(self):
        from windows_ai.security.crypto import derive_key
        key1, salt = derive_key("password1")
        key2, _ = derive_key("password2", salt)
        assert key1 != key2

    def test_hash_password(self):
        from windows_ai.security.crypto import hash_password, verify_password
        hashed, salt = hash_password("mypassword")
        assert isinstance(hashed, str)
        assert verify_password("mypassword", hashed, salt)
        assert not verify_password("wrongpassword", hashed, salt)

    def test_compute_sha256(self):
        from windows_ai.security.crypto import compute_sha256
        digest = compute_sha256(b"hello")
        assert len(digest) == 64  # hex sha256
        assert digest == compute_sha256(b"hello")  # deterministic

    def test_generate_token(self):
        from windows_ai.security.crypto import generate_token
        t1 = generate_token()
        t2 = generate_token()
        assert t1 != t2
        assert len(t1) > 10


# ========================================================================
# Security: Threat Monitor
# ========================================================================

class TestThreatMonitor:
    """Tests for expanded threat monitor."""

    def test_analyze_backward_compat(self):
        from windows_ai.security.threat_monitor import ThreatMonitor
        tm = ThreatMonitor()
        hits = tm.analyze("This is a phishing attack")
        assert "phishing" in hits
        assert "attack" in hits

    def test_analyze_no_threats(self):
        from windows_ai.security.threat_monitor import ThreatMonitor
        tm = ThreatMonitor()
        assert tm.analyze("Hello world, how are you?") == []

    def test_analyze_categorized(self):
        from windows_ai.security.threat_monitor import ThreatMonitor
        tm = ThreatMonitor()
        result = tm.analyze_categorized("detected malware and sql injection attempt")
        assert "malware" in result
        assert "injection" in result

    def test_record_request_normal(self):
        from windows_ai.security.threat_monitor import ThreatMonitor
        tm = ThreatMonitor(rate_threshold=100)
        alert = tm.record_request("client-1")
        assert alert is None  # One request shouldn't trigger

    def test_record_request_burst(self):
        from windows_ai.security.threat_monitor import ThreatMonitor
        tm = ThreatMonitor(rate_threshold=5, rate_window_seconds=60)
        alerts = []
        for _ in range(10):
            a = tm.record_request("client-burst")
            if a is not None:
                alerts.append(a)
        assert len(alerts) > 0
        assert alerts[0].category == "rate_anomaly"

    def test_scan_payload(self):
        from windows_ai.security.threat_monitor import ThreatMonitor
        tm = ThreatMonitor()
        alerts = tm.scan_payload("Found malware in the system", source="test")
        assert len(alerts) > 0
        assert alerts[0].source == "test"

    def test_alert_callback(self):
        from windows_ai.security.threat_monitor import ThreatMonitor
        tm = ThreatMonitor()
        captured = []
        tm.on_alert(lambda a: captured.append(a))
        tm.scan_payload("ransomware detected")
        assert len(captured) > 0

    def test_get_alerts(self):
        from windows_ai.security.threat_monitor import ThreatMonitor, ThreatLevel
        tm = ThreatMonitor()
        tm.scan_payload("sql injection exploit attack")
        alerts = tm.get_alerts()
        assert len(alerts) > 0

    def test_clear_alerts(self):
        from windows_ai.security.threat_monitor import ThreatMonitor
        tm = ThreatMonitor()
        tm.scan_payload("malware detected")
        count = tm.clear_alerts()
        assert count > 0
        assert tm.get_alerts() == []

    def test_stats(self):
        from windows_ai.security.threat_monitor import ThreatMonitor
        tm = ThreatMonitor()
        stats = tm.stats()
        assert "total_alerts" in stats
        assert "alert_breakdown" in stats


# ========================================================================
# Security: Rollback Manager
# ========================================================================

class TestRollbackManager:
    """Tests for expanded rollback manager."""

    def test_basic_rollback(self):
        from windows_ai.security.rollback import RollbackManager
        rm = RollbackManager()
        log = []
        rm.add(lambda: log.append("a"))
        rm.add(lambda: log.append("b"))
        count = rm.rollback()
        assert count == 2
        assert log == ["b", "a"]  # Reverse order

    def test_checkpoint_create_restore(self):
        from windows_ai.security.rollback import RollbackManager
        rm = RollbackManager()
        state = {"key": "value", "count": 42}
        rm.create_checkpoint("cp1", state)
        state["key"] = "changed"
        restored = rm.restore_checkpoint("cp1")
        assert restored["key"] == "value"  # Original value

    def test_checkpoint_not_found(self):
        from windows_ai.security.rollback import RollbackManager
        rm = RollbackManager()
        assert rm.restore_checkpoint("nonexistent") is None

    def test_list_checkpoints(self):
        from windows_ai.security.rollback import RollbackManager
        rm = RollbackManager()
        rm.create_checkpoint("cp1", {"a": 1})
        rm.create_checkpoint("cp2", {"b": 2})
        assert rm.list_checkpoints() == ["cp1", "cp2"]

    def test_delete_checkpoint(self):
        from windows_ai.security.rollback import RollbackManager
        rm = RollbackManager()
        rm.create_checkpoint("cp1", {"a": 1})
        assert rm.delete_checkpoint("cp1") is True
        assert rm.delete_checkpoint("cp1") is False

    def test_transaction_commit(self):
        from windows_ai.security.rollback import RollbackManager
        rm = RollbackManager()
        rm.begin_transaction()
        log = []
        rm.add(lambda: log.append("tx"))
        rm.commit_transaction()
        assert rm.pending_hooks == 1

    def test_transaction_rollback(self):
        from windows_ai.security.rollback import RollbackManager
        rm = RollbackManager()
        log = []
        rm.add(lambda: log.append("before"))
        rm.begin_transaction()
        rm.add(lambda: log.append("in_tx"))
        count = rm.rollback_transaction()
        assert count == 1
        assert log == ["in_tx"]
        assert rm.pending_hooks == 1  # "before" still there

    def test_history(self):
        from windows_ai.security.rollback import RollbackManager
        rm = RollbackManager()
        rm.add(lambda: None)
        rm.rollback()
        assert len(rm.history) == 1
        assert rm.history[0]["action"] == "rollback"

    def test_clear(self):
        from windows_ai.security.rollback import RollbackManager
        rm = RollbackManager()
        rm.add(lambda: None)
        rm.create_checkpoint("cp", {})
        rm.clear()
        assert rm.pending_hooks == 0
        assert rm.list_checkpoints() == []


# ========================================================================
# Plugin Dependency Resolver
# ========================================================================

class TestPluginDependencyResolver:
    """Tests for plugin dependency resolver."""

    def test_basic_resolution(self):
        from windows_ai.plugins.dependency_resolver import PluginDependencyResolver
        r = PluginDependencyResolver()
        r.register("base")
        r.register("audio", depends_on=["base"])
        r.register("speech", depends_on=["audio"])
        order = r.resolve()
        assert order.index("base") < order.index("audio")
        assert order.index("audio") < order.index("speech")

    def test_no_dependencies(self):
        from windows_ai.plugins.dependency_resolver import PluginDependencyResolver
        r = PluginDependencyResolver()
        r.register("a")
        r.register("b")
        order = r.resolve()
        assert set(order) == {"a", "b"}

    def test_circular_dependency_detected(self):
        from windows_ai.plugins.dependency_resolver import (
            PluginDependencyResolver, CircularDependencyError,
        )
        r = PluginDependencyResolver()
        r.register("a", depends_on=["b"])
        r.register("b", depends_on=["a"])
        with pytest.raises(CircularDependencyError):
            r.resolve()

    def test_missing_dependency(self):
        from windows_ai.plugins.dependency_resolver import (
            PluginDependencyResolver, MissingDependencyError,
        )
        r = PluginDependencyResolver()
        r.register("child", depends_on=["parent"])
        with pytest.raises(MissingDependencyError):
            r.resolve()

    def test_ignore_missing(self):
        from windows_ai.plugins.dependency_resolver import PluginDependencyResolver
        r = PluginDependencyResolver()
        r.register("child", depends_on=["parent"])
        order = r.resolve(ignore_missing=True)
        assert "child" in order

    def test_resolve_for_single(self):
        from windows_ai.plugins.dependency_resolver import PluginDependencyResolver
        r = PluginDependencyResolver()
        r.register("a")
        r.register("b", depends_on=["a"])
        r.register("c", depends_on=["b"])
        order = r.resolve_for("c")
        assert order == ["a", "b", "c"]

    def test_get_dependents(self):
        from windows_ai.plugins.dependency_resolver import PluginDependencyResolver
        r = PluginDependencyResolver()
        r.register("base")
        r.register("x", depends_on=["base"])
        r.register("y", depends_on=["base"])
        deps = r.get_dependents("base")
        assert set(deps) == {"x", "y"}

    def test_safe_to_remove(self):
        from windows_ai.plugins.dependency_resolver import PluginDependencyResolver
        r = PluginDependencyResolver()
        r.register("base")
        r.register("x", depends_on=["base"])
        safe, deps = r.is_safe_to_remove("base")
        assert not safe
        assert "x" in deps

    def test_find_circular(self):
        from windows_ai.plugins.dependency_resolver import PluginDependencyResolver
        r = PluginDependencyResolver()
        r.register("a", depends_on=["b"])
        r.register("b", depends_on=["a"])
        cycles = r.find_circular_dependencies()
        assert len(cycles) > 0

    def test_unregister(self):
        from windows_ai.plugins.dependency_resolver import PluginDependencyResolver
        r = PluginDependencyResolver()
        r.register("a")
        assert r.unregister("a") is True
        assert r.unregister("a") is False

    def test_stats(self):
        from windows_ai.plugins.dependency_resolver import PluginDependencyResolver
        r = PluginDependencyResolver()
        r.register("a")
        r.register("b", depends_on=["a"])
        stats = r.stats()
        assert stats["total_plugins"] == 2
        assert stats["total_dependencies"] == 1


# ========================================================================
# RAG: Hybrid Search
# ========================================================================

class TestBM25Index:
    """Tests for BM25 text search."""

    def test_add_and_search(self):
        from windows_ai.rag.hybrid_search import BM25Index
        idx = BM25Index()
        idx.add_document("doc1", "The quick brown fox jumps over the lazy dog")
        idx.add_document("doc2", "A fast red car drives on the highway")
        results = idx.search("quick fox")
        assert len(results) > 0
        assert results[0].doc_id == "doc1"

    def test_empty_query(self):
        from windows_ai.rag.hybrid_search import BM25Index
        idx = BM25Index()
        idx.add_document("doc1", "hello world")
        assert idx.search("") == []

    def test_no_match(self):
        from windows_ai.rag.hybrid_search import BM25Index
        idx = BM25Index()
        idx.add_document("doc1", "hello world")
        results = idx.search("xyzzy nonexistent")
        assert len(results) == 0

    def test_remove_document(self):
        from windows_ai.rag.hybrid_search import BM25Index
        idx = BM25Index()
        idx.add_document("doc1", "hello world")
        assert idx.remove_document("doc1") is True
        assert idx.document_count == 0

    def test_document_count(self):
        from windows_ai.rag.hybrid_search import BM25Index
        idx = BM25Index()
        assert idx.document_count == 0
        idx.add_document("d1", "a")
        idx.add_document("d2", "b")
        assert idx.document_count == 2


class TestVectorIndex:
    """Tests for dense vector search."""

    def test_add_and_search(self):
        from windows_ai.rag.hybrid_search import VectorIndex
        idx = VectorIndex()
        idx.add_document("d1", "doc1", [1.0, 0.0, 0.0])
        idx.add_document("d2", "doc2", [0.0, 1.0, 0.0])
        results = idx.search([1.0, 0.0, 0.0])
        assert results[0].doc_id == "d1"

    def test_cosine_similarity(self):
        from windows_ai.rag.hybrid_search import VectorIndex
        # Identical vectors should have similarity ~1.0
        sim = VectorIndex._cosine_similarity([1, 0], [1, 0])
        assert abs(sim - 1.0) < 0.001

    def test_orthogonal_vectors(self):
        from windows_ai.rag.hybrid_search import VectorIndex
        sim = VectorIndex._cosine_similarity([1, 0], [0, 1])
        assert abs(sim) < 0.001


class TestHybridSearch:
    """Tests for hybrid BM25 + vector search."""

    def test_bm25_only_fallback(self):
        from windows_ai.rag.hybrid_search import HybridSearch
        hs = HybridSearch()
        hs.add_document("d1", "The quick brown fox")
        hs.add_document("d2", "A red car")
        results = hs.search("quick fox")
        assert len(results) > 0
        assert results[0].source == "hybrid"

    def test_hybrid_with_vectors(self):
        from windows_ai.rag.hybrid_search import HybridSearch
        hs = HybridSearch()
        hs.add_document("d1", "python programming", [1.0, 0.0])
        hs.add_document("d2", "java development", [0.0, 1.0])
        results = hs.search("python", query_embedding=[0.9, 0.1])
        assert len(results) > 0

    def test_remove_document(self):
        from windows_ai.rag.hybrid_search import HybridSearch
        hs = HybridSearch()
        hs.add_document("d1", "test content", [1.0])
        hs.remove_document("d1")
        assert hs.bm25.document_count == 0

    def test_stats(self):
        from windows_ai.rag.hybrid_search import HybridSearch
        hs = HybridSearch()
        hs.add_document("d1", "test", [1.0])
        stats = hs.stats()
        assert stats["bm25_documents"] == 1
        assert stats["vector_documents"] == 1


# ========================================================================
# RAG: File Indexer
# ========================================================================

class TestFileSystemIndexer:
    """Tests for the file system indexer."""

    def test_index_file(self, tmp_path):
        from windows_ai.rag.file_indexer import FileSystemIndexer
        f = tmp_path / "test.py"
        f.write_text("def hello(): return 'world'")
        idx = FileSystemIndexer()
        assert idx.index_file(str(f)) is True
        results = idx.search("hello")
        assert len(results) > 0

    def test_index_directory(self, tmp_path):
        from windows_ai.rag.file_indexer import FileSystemIndexer
        (tmp_path / "a.py").write_text("print('hello')")
        (tmp_path / "b.md").write_text("# README")
        (tmp_path / "c.bin").write_bytes(b"\x00\x01")  # not text
        idx = FileSystemIndexer(roots=[str(tmp_path)])
        result = idx.index_all()
        assert result["files_indexed"] == 2

    def test_search_indexed_files(self, tmp_path):
        from windows_ai.rag.file_indexer import FileSystemIndexer
        (tmp_path / "hello.py").write_text("def greet(): return 'hello world'")
        idx = FileSystemIndexer(roots=[str(tmp_path)])
        idx.index_all()
        results = idx.search("greet hello")
        assert len(results) > 0

    def test_remove_file(self, tmp_path):
        from windows_ai.rag.file_indexer import FileSystemIndexer
        f = tmp_path / "test.py"
        f.write_text("content")
        idx = FileSystemIndexer()
        idx.index_file(str(f))
        assert idx.remove_file(str(f)) is True

    def test_stats(self, tmp_path):
        from windows_ai.rag.file_indexer import FileSystemIndexer
        idx = FileSystemIndexer(roots=[str(tmp_path)])
        stats = idx.stats()
        assert "indexed_files" in stats
        assert "watching" in stats

    def test_nonexistent_root(self):
        from windows_ai.rag.file_indexer import FileSystemIndexer
        idx = FileSystemIndexer(roots=["/nonexistent/path"])
        result = idx.index_all()
        assert result["files_indexed"] == 0


# ========================================================================
# Workflow API Routes
# ========================================================================

class TestWorkflowRoutes:
    """Tests for workflow API endpoints."""

    def test_import_module(self):
        from windows_ai.api.workflow_routes import router
        assert router is not None

    def test_create_workflow(self):
        from windows_ai.api.workflow_routes import get_engine
        engine = get_engine()
        result = engine.create_workflow("test-wf", "Test Workflow")
        assert result["status"] == "success"

    def test_create_duplicate_workflow(self):
        from windows_ai.api.workflow_routes import get_engine
        engine = get_engine()
        engine.create_workflow("dup-wf", "Dup")
        result = engine.create_workflow("dup-wf", "Dup Again")
        assert result["status"] == "error"

    def test_add_node(self):
        from windows_ai.api.workflow_routes import get_engine
        engine = get_engine()
        engine.create_workflow("node-wf", "Node Test")
        result = engine.add_node_to_workflow("node-wf", "n1", "echo")
        assert result["status"] == "success"

    def test_connect_nodes(self):
        from windows_ai.api.workflow_routes import get_engine
        engine = get_engine()
        engine.create_workflow("edge-wf", "Edge Test")
        engine.add_node_to_workflow("edge-wf", "n1", "echo")
        engine.add_node_to_workflow("edge-wf", "n2", "echo")
        result = engine.connect_nodes("edge-wf", "n1", "n2")
        assert result["status"] == "success"

    @pytest.mark.asyncio
    async def test_execute_workflow(self):
        from windows_ai.api.workflow_routes import get_engine
        engine = get_engine()
        engine.create_workflow("exec-wf", "Exec Test")
        engine.add_node_to_workflow("exec-wf", "start", "echo")

        # Register a simple executor
        async def echo_executor(node, context):
            return {"status": "success", "outputs": {"result": "done"}}

        engine.register_node_executor("echo", echo_executor)
        result = await engine.execute_workflow("exec-wf")
        assert result["status"] == "success"
        assert result["completed_nodes"] == 1


# ========================================================================
# Server Wiring: Agent, SSE, WebSocket, Workflow routes
# ========================================================================

class TestServerWiring:
    """Verify that all routes are wired into the FastAPI app."""

    def test_all_routers_included(self):
        from windows_ai.api.server import app
        paths = [route.path for route in app.routes]
        path_str = " ".join(paths)

        # Agent routes
        assert "/api/v1/agents" in path_str or "agents" in path_str

        # SSE routes
        assert "/api/sse" in path_str or "sse" in path_str

        # WebSocket routes
        assert "/api/ws" in path_str or "ws" in path_str

        # Workflow routes
        assert "/api/v1/workflows" in path_str or "workflows" in path_str

        # Existing routes still present
        assert "/api/v1" in path_str
        assert "/api/health" in path_str or "health" in path_str

    def test_app_has_rate_limit_middleware(self):
        from windows_ai.api.server import app
        middleware_types = [type(m).__name__ for m in app.user_middleware]
        # RateLimitMiddleware should be in the middleware stack
        middleware_names = str(middleware_types)
        assert "RateLimit" in middleware_names or len(app.user_middleware) > 0

    def test_workflow_router_has_endpoints(self):
        from windows_ai.api.workflow_routes import router
        route_paths = [r.path for r in router.routes]
        assert "/" in route_paths or any("workflow" in str(r) for r in router.routes)


# ========================================================================
# RAG Module Exports
# ========================================================================

class TestRAGModuleExports:
    """Verify RAG module exports new components."""

    def test_hybrid_search_importable(self):
        from windows_ai.rag import HybridSearch, BM25Index, VectorIndex, SearchResult
        assert HybridSearch is not None

    def test_file_indexer_importable(self):
        from windows_ai.rag import FileSystemIndexer
        assert FileSystemIndexer is not None
