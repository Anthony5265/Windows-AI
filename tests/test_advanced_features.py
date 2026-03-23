"""Tests for lazy loader, plugin search, and crash recovery."""
import pytest
import asyncio
import time


# ========================================================================
# Lazy Manager Loader
# ========================================================================

class TestLazyManagerLoader:
    """Tests for lazy-loading integration managers."""

    @pytest.mark.asyncio
    async def test_get_unknown_manager_raises(self):
        from windows_ai.core.lazy_loader import LazyManagerLoader
        loader = LazyManagerLoader()
        with pytest.raises(KeyError):
            await loader.get("nonexistent_manager")

    def test_available_managers_list(self):
        from windows_ai.core.lazy_loader import LazyManagerLoader
        loader = LazyManagerLoader()
        managers = loader.available_managers
        assert "ai" in managers
        assert "audio" in managers
        assert "rag" in managers
        assert len(managers) >= 40

    def test_is_loaded_before_get(self):
        from windows_ai.core.lazy_loader import LazyManagerLoader
        loader = LazyManagerLoader()
        assert loader.is_loaded("ai") is False

    def test_stats_initial(self):
        from windows_ai.core.lazy_loader import LazyManagerLoader
        loader = LazyManagerLoader()
        stats = loader.stats()
        assert stats["total_available"] >= 40
        assert stats["total_loaded"] == 0

    @pytest.mark.asyncio
    async def test_lazy_load_manager(self):
        from windows_ai.core.lazy_loader import LazyManagerLoader
        loader = LazyManagerLoader()
        # Load a lightweight manager
        manager = await loader.get("scheduling")
        assert manager is not None
        assert loader.is_loaded("scheduling")

    @pytest.mark.asyncio
    async def test_double_get_returns_same(self):
        from windows_ai.core.lazy_loader import LazyManagerLoader
        loader = LazyManagerLoader()
        m1 = await loader.get("notifications")
        m2 = await loader.get("notifications")
        assert m1 is m2


# ========================================================================
# Plugin Search Index
# ========================================================================

class TestPluginSearchIndex:
    """Tests for semantic search over plugin documentation."""

    def test_index_and_search(self):
        from windows_ai.search.plugin_search import PluginSearchIndex
        idx = PluginSearchIndex()
        idx.index_plugin({
            "id": "whisper",
            "name": "Whisper Speech to Text",
            "description": "Transcribe audio using OpenAI Whisper",
            "tags": ["audio", "transcription", "speech"],
        })
        idx.index_plugin({
            "id": "dalle",
            "name": "DALL-E Image Generator",
            "description": "Generate images from text prompts",
            "tags": ["image", "generation"],
        })
        results = idx.search("transcribe audio speech")
        assert len(results) > 0
        assert results[0].doc_id == "whisper"

    def test_search_by_tags(self):
        from windows_ai.search.plugin_search import PluginSearchIndex
        idx = PluginSearchIndex()
        idx.index_plugin({
            "id": "p1",
            "name": "Audio Plugin",
            "tags": ["audio", "speech"],
        })
        results = idx.search_by_tags(["audio"])
        assert len(results) > 0

    def test_search_by_capability(self):
        from windows_ai.search.plugin_search import PluginSearchIndex
        idx = PluginSearchIndex()
        idx.index_plugin({
            "id": "p1",
            "name": "Code Completer",
            "capabilities": ["code-completion", "code-review"],
        })
        results = idx.search_by_capability("code-completion")
        assert len(results) > 0

    def test_index_batch(self):
        from windows_ai.search.plugin_search import PluginSearchIndex
        idx = PluginSearchIndex()
        plugins = [
            {"id": f"plugin-{i}", "name": f"Plugin {i}", "description": f"Does thing {i}"}
            for i in range(10)
        ]
        count = idx.index_plugins(plugins)
        assert count == 10
        assert idx.count == 10

    def test_remove_plugin(self):
        from windows_ai.search.plugin_search import PluginSearchIndex
        idx = PluginSearchIndex()
        idx.index_plugin({"id": "test", "name": "Test"})
        assert idx.remove_plugin("test") is True
        assert idx.count == 0

    def test_get_plugin(self):
        from windows_ai.search.plugin_search import PluginSearchIndex
        idx = PluginSearchIndex()
        idx.index_plugin({"id": "p1", "name": "Plugin One", "tags": ["test"]})
        data = idx.get_plugin("p1")
        assert data["name"] == "Plugin One"

    def test_list_all(self):
        from windows_ai.search.plugin_search import PluginSearchIndex
        idx = PluginSearchIndex()
        idx.index_plugin({"id": "a", "name": "A"})
        idx.index_plugin({"id": "b", "name": "B"})
        assert len(idx.list_all()) == 2

    def test_stats(self):
        from windows_ai.search.plugin_search import PluginSearchIndex
        idx = PluginSearchIndex()
        idx.index_plugin({"id": "p1", "name": "P1", "tags": ["audio"]})
        stats = idx.stats()
        assert stats["indexed_plugins"] == 1
        assert stats["unique_tags"] == 1

    def test_empty_id_rejected(self):
        from windows_ai.search.plugin_search import PluginSearchIndex
        idx = PluginSearchIndex()
        assert idx.index_plugin({"id": "", "name": "No ID"}) is False
        assert idx.count == 0


# ========================================================================
# Crash Recovery Manager
# ========================================================================

class TestCrashRecoveryManager:
    """Tests for automatic crash recovery."""

    def test_register_component(self):
        from windows_ai.core.crash_recovery import CrashRecoveryManager
        mgr = CrashRecoveryManager()
        mgr.register("api_server")
        stats = mgr.stats()
        assert stats["monitored_components"] == 1
        assert stats["healthy"] == 1

    def test_heartbeat(self):
        from windows_ai.core.crash_recovery import (
            CrashRecoveryManager, ComponentStatus,
        )
        mgr = CrashRecoveryManager()
        mgr.register("service")
        mgr.heartbeat("service")
        status = mgr.get_component_status("service")
        assert status["status"] == ComponentStatus.HEALTHY.value

    @pytest.mark.asyncio
    async def test_detect_timeout(self):
        from windows_ai.core.crash_recovery import (
            CrashRecoveryManager, ComponentStatus,
        )
        mgr = CrashRecoveryManager(heartbeat_timeout=0.01)
        mgr.register("slow_service")
        # Force the heartbeat to be old
        mgr._components["slow_service"].last_heartbeat = time.time() - 1.0
        statuses = await mgr.check_health()
        assert statuses["slow_service"] == ComponentStatus.FAILED

    @pytest.mark.asyncio
    async def test_recover_failed(self):
        from windows_ai.core.crash_recovery import CrashRecoveryManager
        recovered = False

        async def restart():
            nonlocal recovered
            recovered = True

        mgr = CrashRecoveryManager(heartbeat_timeout=0.01, base_backoff=0.01)
        mgr.register("failing", restart_fn=restart)
        mgr.report_failure("failing", "test error")
        results = await mgr.recover_failed()
        assert results["failing"] is True
        assert recovered is True

    @pytest.mark.asyncio
    async def test_max_retries_exceeded(self):
        from windows_ai.core.crash_recovery import CrashRecoveryManager

        async def restart():
            raise RuntimeError("Always fails")

        mgr = CrashRecoveryManager(max_retries=2, base_backoff=0.01)
        mgr.register("broken", restart_fn=restart)
        mgr._components["broken"].failure_count = 10
        mgr.report_failure("broken", "test")
        results = await mgr.recover_failed()
        assert results["broken"] is False

    def test_report_failure(self):
        from windows_ai.core.crash_recovery import (
            CrashRecoveryManager, ComponentStatus,
        )
        mgr = CrashRecoveryManager()
        mgr.register("comp")
        mgr.report_failure("comp", "some error")
        status = mgr.get_component_status("comp")
        assert status["status"] == ComponentStatus.FAILED.value
        assert status["last_error"] == "some error"

    def test_unregister(self):
        from windows_ai.core.crash_recovery import CrashRecoveryManager
        mgr = CrashRecoveryManager()
        mgr.register("temp")
        assert mgr.unregister("temp") is True
        assert mgr.unregister("temp") is False

    def test_history(self):
        from windows_ai.core.crash_recovery import CrashRecoveryManager
        mgr = CrashRecoveryManager()
        mgr.register("comp")
        mgr.report_failure("comp", "err")
        assert len(mgr.history) == 1
        assert mgr.history[0]["event"] == "failure_reported"

    def test_stats(self):
        from windows_ai.core.crash_recovery import CrashRecoveryManager
        mgr = CrashRecoveryManager()
        mgr.register("a")
        mgr.register("b")
        stats = mgr.stats()
        assert stats["monitored_components"] == 2
        assert stats["healthy"] == 2

    def test_get_component_status_not_found(self):
        from windows_ai.core.crash_recovery import CrashRecoveryManager
        mgr = CrashRecoveryManager()
        assert mgr.get_component_status("none") is None
