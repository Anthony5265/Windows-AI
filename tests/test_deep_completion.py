"""
Tests for observability routes, mesh routes, and deeper module validation.
"""
import pytest
import asyncio


# ========================================================================
# Observability Routes (via TestClient)
# ========================================================================

class TestObservabilityRoutes:
    """Test observability REST endpoints."""

    def test_import_routes(self):
        from windows_ai.api.observability_routes import router
        assert router is not None
        assert router.prefix == "/api/observability"

    @pytest.mark.asyncio
    async def test_dashboard_endpoint(self):
        from windows_ai.api.observability_routes import get_dashboard
        result = await get_dashboard()
        assert result["status"] == "success"
        assert "tracing" in result
        assert "metrics" in result
        assert "logging" in result

    @pytest.mark.asyncio
    async def test_trace_stats(self):
        from windows_ai.api.observability_routes import get_trace_stats
        result = await get_trace_stats()
        assert result["status"] == "success"
        assert "total_spans" in result

    @pytest.mark.asyncio
    async def test_get_recent_traces(self):
        from windows_ai.api.observability_routes import get_recent_traces
        result = await get_recent_traces(limit=10)
        assert result["status"] == "success"
        assert "spans" in result

    @pytest.mark.asyncio
    async def test_get_all_metrics(self):
        from windows_ai.api.observability_routes import get_all_metrics
        result = await get_all_metrics()
        assert result["status"] == "success"
        assert "metrics" in result

    @pytest.mark.asyncio
    async def test_metrics_stats(self):
        from windows_ai.api.observability_routes import get_metrics_stats
        result = await get_metrics_stats()
        assert result["status"] == "success"
        assert "total_metrics" in result

    @pytest.mark.asyncio
    async def test_increment_counter(self):
        from windows_ai.api.observability_routes import increment_counter, MetricIncrementRequest
        req = MetricIncrementRequest(name="test_counter", amount=5)
        result = await increment_counter(req)
        assert result["status"] == "success"
        assert result["value"] >= 5

    @pytest.mark.asyncio
    async def test_set_gauge(self):
        from windows_ai.api.observability_routes import set_gauge, GaugeSetRequest
        req = GaugeSetRequest(name="test_gauge", value=42.0)
        result = await set_gauge(req)
        assert result["status"] == "success"
        assert result["value"] == 42.0

    @pytest.mark.asyncio
    async def test_observe_histogram(self):
        from windows_ai.api.observability_routes import observe_histogram, HistogramObserveRequest
        req = HistogramObserveRequest(name="test_hist", value=0.5)
        result = await observe_histogram(req)
        assert result["status"] == "success"

    @pytest.mark.asyncio
    async def test_get_logs(self):
        from windows_ai.api.observability_routes import get_logs
        result = await get_logs(limit=10)
        assert result["status"] == "success"
        assert "entries" in result

    @pytest.mark.asyncio
    async def test_log_stats(self):
        from windows_ai.api.observability_routes import get_log_stats
        result = await get_log_stats()
        assert result["status"] == "success"
        assert "total_entries" in result


# ========================================================================
# Mesh Routes
# ========================================================================

class TestMeshRoutes:
    """Test mesh network REST endpoints."""

    def test_import_routes(self):
        from windows_ai.api.mesh_routes import router
        assert router is not None
        assert router.prefix == "/api/mesh"

    @pytest.mark.asyncio
    async def test_mesh_status(self):
        from windows_ai.api.mesh_routes import get_mesh_status
        result = await get_mesh_status()
        assert result["status"] == "success"
        assert "node_id" in result

    @pytest.mark.asyncio
    async def test_get_peers(self):
        from windows_ai.api.mesh_routes import get_peers
        result = await get_peers()
        assert result["status"] == "success"
        assert "peers" in result

    @pytest.mark.asyncio
    async def test_add_peer(self):
        from windows_ai.api.mesh_routes import add_peer, AddPeerRequest
        req = AddPeerRequest(node_id="peer-1", address="127.0.0.1", port=9999)
        result = await add_peer(req)
        assert result["status"] == "success"

    @pytest.mark.asyncio
    async def test_get_all_state(self):
        from windows_ai.api.mesh_routes import get_all_state
        result = await get_all_state()
        assert result["status"] == "success"

    @pytest.mark.asyncio
    async def test_set_and_get_state(self):
        from windows_ai.api.mesh_routes import set_state, get_state, StateSetRequest
        await set_state(StateSetRequest(key="test_key", value="test_value"))
        result = await get_state("test_key")
        assert result["status"] == "success"
        assert result["value"] == "test_value"

    @pytest.mark.asyncio
    async def test_submit_task(self):
        from windows_ai.api.mesh_routes import submit_task, TaskSubmitRequest
        req = TaskSubmitRequest(task_type="test_task", payload={"data": "hello"})
        result = await submit_task(req)
        assert result["status"] == "success"
        assert "task_id" in result

    @pytest.mark.asyncio
    async def test_queue_status(self):
        from windows_ai.api.mesh_routes import get_queue_status
        result = await get_queue_status()
        assert result["status"] == "success"

    @pytest.mark.asyncio
    async def test_distribute_inference(self):
        from windows_ai.api.mesh_routes import distribute_inference, InferenceRequest
        req = InferenceRequest(model="gpt-4", prompt="Hello world")
        result = await distribute_inference(req)
        assert result["status"] == "success"

    @pytest.mark.asyncio
    async def test_rag_search(self):
        from windows_ai.api.mesh_routes import distribute_rag_search, RAGSearchRequest
        req = RAGSearchRequest(query="test query", top_k=3)
        result = await distribute_rag_search(req)
        assert result["status"] == "success"

    @pytest.mark.asyncio
    async def test_execute_pipeline(self):
        from windows_ai.api.mesh_routes import execute_pipeline, PipelineRequest
        req = PipelineRequest(
            pipeline_id="test-pipe",
            steps=[{"task_type": "ai_inference", "payload": {"prompt": "step1"}}],
        )
        result = await execute_pipeline(req)
        assert result["status"] == "success"
        assert result["steps_completed"] == 1

    @pytest.mark.asyncio
    async def test_get_capabilities(self):
        from windows_ai.api.mesh_routes import get_capabilities
        result = await get_capabilities()
        assert result["status"] == "success"
        assert "capabilities" in result

    @pytest.mark.asyncio
    async def test_coordinator_stats(self):
        from windows_ai.api.mesh_routes import get_coordinator_stats
        result = await get_coordinator_stats()
        assert result["status"] == "success"


# ========================================================================
# Plugin Lifecycle Manager
# ========================================================================

class TestPluginLifecycle:
    """Test plugin lifecycle management."""

    def test_import(self):
        from windows_ai.core.plugin_lifecycle import PluginLifecycleManager, PluginState
        assert PluginState.INSTALLED is not None
        assert PluginState.ENABLED is not None

    def test_lifecycle_manager_creation(self):
        from windows_ai.core.plugin_lifecycle import PluginLifecycleManager
        from unittest.mock import MagicMock
        plm = PluginLifecycleManager(credential_manager=MagicMock())
        assert plm is not None

    def test_plugin_state_enum(self):
        from windows_ai.core.plugin_lifecycle import PluginState
        assert PluginState.UNINSTALLED.value == "uninstalled"
        assert PluginState.INSTALLED.value == "installed"
        assert PluginState.ENABLED.value == "enabled"
        assert PluginState.DISABLED.value == "disabled"
        assert PluginState.ERROR.value == "error"


# ========================================================================
# Cloud Sync Module
# ========================================================================

class TestCloudSync:
    """Test cloud sync components."""

    def test_import_models(self):
        from windows_ai.cloud_sync.models import DataCategory, SyncState
        assert DataCategory is not None
        assert SyncState is not None

    def test_import_encryption(self):
        from windows_ai.cloud_sync.encryption import SyncEncryption
        assert SyncEncryption is not None

    def test_sync_encryption(self):
        from windows_ai.cloud_sync.encryption import SyncEncryption
        enc = SyncEncryption()
        encoded = enc.encode_base64(b"hello world")
        decoded = enc.decode_base64(encoded)
        assert decoded == b"hello world" or decoded == "hello world"


# ========================================================================
# Database Module
# ========================================================================

class TestDatabaseModule:
    """Test database optimization modules."""

    def test_import_connection_pool(self):
        from windows_ai.database.connection_pool import ConnectionPool
        assert ConnectionPool is not None

    def test_import_query_optimizer(self):
        try:
            from windows_ai.database.query_optimizer import QueryOptimizer
            assert QueryOptimizer is not None
        except ImportError:
            pytest.skip("sqlalchemy not installed")

    def test_import_transaction_optimizer(self):
        try:
            from windows_ai.database.transaction_optimizer import TransactionOptimizer
            assert TransactionOptimizer is not None
        except ImportError:
            pytest.skip("sqlalchemy not installed")

    def test_import_index_strategy(self):
        try:
            from windows_ai.database.index_strategy import IndexStrategy
            assert IndexStrategy is not None
        except ImportError:
            pytest.skip("sqlalchemy not installed")


# ========================================================================
# Updater Module
# ========================================================================

class TestUpdaterModule:
    """Test updater system."""

    def test_import_update_client(self):
        from windows_ai.updater.update_client import UpdateClient
        assert UpdateClient is not None

    def test_import_version_manager(self):
        from windows_ai.updater.version_manager import VersionManager
        assert VersionManager is not None

    def test_version_manager_creation(self):
        from windows_ai.updater.version_manager import VersionManager
        vm = VersionManager()
        assert vm is not None


# ========================================================================
# Analytics Module
# ========================================================================

class TestAnalyticsModule:
    """Test analytics components."""

    def test_import_anomaly_detection(self):
        from windows_ai.analytics.anomaly_detection import AdvancedAnalytics
        assert AdvancedAnalytics is not None

    def test_import_predictive(self):
        from windows_ai.analytics.predictive_analytics import PredictiveAnalytics
        assert PredictiveAnalytics is not None

    def test_anomaly_detector_creation(self):
        from windows_ai.analytics.anomaly_detection import AdvancedAnalytics
        ad = AdvancedAnalytics()
        assert ad is not None


# ========================================================================
# Monitoring Module
# ========================================================================

class TestMonitoringModule:
    """Test monitoring dashboard."""

    def test_import_dashboard(self):
        from windows_ai.monitoring.dashboard import MonitoringDashboard
        assert MonitoringDashboard is not None

    def test_dashboard_creation(self):
        from windows_ai.monitoring.dashboard import MonitoringDashboard
        dashboard = MonitoringDashboard()
        assert dashboard is not None


# ========================================================================
# Server Router Registration
# ========================================================================

class TestServerRegistration:
    """Verify all routers are registered in server.py."""

    def test_app_exists(self):
        from windows_ai.api.server import app
        assert app is not None

    def test_all_routes_registered(self):
        from windows_ai.api.server import app
        routes = [r.path for r in app.routes]
        # Check key prefixes exist
        route_str = str(routes)
        assert "/api/v1" in route_str or "plugins" in route_str
        assert "/api/health" in route_str or "health" in route_str

    def test_observability_router_imported(self):
        from windows_ai.api.server import observability_router
        assert observability_router is not None

    def test_mesh_router_imported(self):
        from windows_ai.api.server import mesh_router
        assert mesh_router is not None


# ========================================================================
# Workflow Engine
# ========================================================================

class TestWorkflowEngine:
    """Test workflow engine components."""

    def test_import(self):
        from windows_ai.workflow.engine import WorkflowEngine, WorkflowNode, WorkflowEdge, Workflow
        assert WorkflowEngine is not None
        assert WorkflowNode is not None

    def test_create_node(self):
        from windows_ai.workflow.engine import WorkflowNode
        node = WorkflowNode("n1", "action", config={"timeout": 30})
        d = node.to_dict()
        assert d["node_id"] == "n1"
        assert d["node_type"] == "action"

    def test_create_edge(self):
        from windows_ai.workflow.engine import WorkflowEdge
        edge = WorkflowEdge("n1", "n2", condition="success")
        d = edge.to_dict()
        assert d["from"] == "n1"
        assert d["to"] == "n2"

    def test_create_workflow(self):
        from windows_ai.workflow.engine import Workflow
        wf = Workflow("wf1", "Test Workflow")
        assert wf.workflow_id == "wf1"
        assert wf.name == "Test Workflow"


# ========================================================================
# Vector DB Interface
# ========================================================================

class TestVectorDB:
    """Test vector database unified interface."""

    def test_import_manager(self):
        from windows_ai.vector_db import VectorDBManager
        assert VectorDBManager is not None

    def test_list_providers(self):
        from windows_ai.vector_db import VectorDBManager
        mgr = VectorDBManager()
        providers = mgr.list_providers()
        assert isinstance(providers, list)
        assert len(providers) >= 3

    def test_create_config(self):
        from windows_ai.vector_db import VectorDBManager
        mgr = VectorDBManager()
        config = mgr.create_config("chroma", 768)
        assert config is not None


# ========================================================================
# Security - RBAC
# ========================================================================

class TestRBAC:
    """Test RBAC system."""

    def test_import(self):
        from windows_ai.security.advanced_rbac import AdvancedRBAC
        assert AdvancedRBAC is not None

    def test_rbac_creation(self):
        from windows_ai.security.advanced_rbac import AdvancedRBAC
        rbac = AdvancedRBAC()
        assert rbac is not None


# ========================================================================
# Security - SSO Integration
# ========================================================================

class TestSSOIntegration:
    """Test SSO integration."""

    def test_import(self):
        from windows_ai.security.sso_integration import SSOIntegration
        assert SSOIntegration is not None
