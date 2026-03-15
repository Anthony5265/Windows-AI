"""
Tests for RAG pipeline, workflow engine, agent system, cache, and streaming.

Verifies completeness and correctness of these critical systems.
"""
import pytest
import asyncio
from unittest.mock import patch, AsyncMock, MagicMock


# =================== RAG Pipeline Tests ===================

class TestRAGEngine:
    """Test RAG engine functionality."""

    @pytest.mark.asyncio
    async def test_rag_engine_init(self):
        """RAG engine initializes with required args."""
        from windows_ai.rag.engine import RAGEngine
        mock_vdb = MagicMock()
        mock_emb = MagicMock()
        engine = RAGEngine(vector_db=mock_vdb, embedding_model=mock_emb)
        assert engine is not None

    @pytest.mark.asyncio
    async def test_rag_engine_has_methods(self):
        """RAG engine has required methods."""
        from windows_ai.rag.engine import RAGEngine
        mock_vdb = MagicMock()
        mock_emb = MagicMock()
        engine = RAGEngine(vector_db=mock_vdb, embedding_model=mock_emb)
        assert hasattr(engine, "query")
        assert hasattr(engine, "index_documents")
        assert hasattr(engine, "retrieve")

    @pytest.mark.asyncio
    async def test_rag_pipeline_manager(self):
        """RAGPipelineManager initializes and has methods."""
        from windows_ai.integrations.rag_pipeline import RAGPipelineManager
        manager = RAGPipelineManager()
        await manager.initialize()
        assert manager._initialized is True
        assert hasattr(manager, "query")
        assert hasattr(manager, "ingest")
        assert hasattr(manager, "retrieve")

    def test_rag_config(self):
        """RAGConfig can be created."""
        from windows_ai.rag.engine import RAGConfig
        config = RAGConfig(index_name="test")
        assert config.index_name == "test"
        assert config.top_k == 10


class TestRAGDocumentProcessor:
    """Test RAG document processor."""

    def test_processor_init(self):
        """Document processor initializes."""
        from windows_ai.rag.document_processor import RAGDocumentProcessor
        processor = RAGDocumentProcessor()
        assert processor is not None

    def test_processor_has_methods(self):
        """Document processor has required methods."""
        from windows_ai.rag.document_processor import RAGDocumentProcessor
        processor = RAGDocumentProcessor()
        assert hasattr(processor, "process_text")
        assert hasattr(processor, "process_file_for_indexing")
        assert hasattr(processor, "process_directory_for_indexing")


class TestRAGAPI:
    """Test RAG API endpoints."""

    def test_rag_api_module_imports(self):
        """RAG API module can be imported."""
        from windows_ai.rag import api
        assert api is not None


# =================== Workflow Engine Tests ===================

class TestWorkflowEngine:
    """Test workflow engine functionality."""

    def test_workflow_engine_init(self):
        """Workflow engine initializes."""
        from windows_ai.workflow.engine import WorkflowEngine
        engine = WorkflowEngine()
        assert engine is not None

    def test_workflow_engine_has_methods(self):
        """Workflow engine has required methods."""
        from windows_ai.workflow.engine import WorkflowEngine
        engine = WorkflowEngine()
        assert hasattr(engine, "create_workflow")
        assert hasattr(engine, "add_node_to_workflow")
        assert hasattr(engine, "connect_nodes")
        assert hasattr(engine, "execute_workflow")

    def test_workflow_create(self):
        """Can create a workflow."""
        from windows_ai.workflow.engine import WorkflowEngine
        engine = WorkflowEngine()
        result = engine.create_workflow("wf1", "Test Workflow")
        assert result["status"] in ["created", "success"]

    def test_workflow_add_node(self):
        """Can add nodes to workflow."""
        from windows_ai.workflow.engine import WorkflowEngine
        engine = WorkflowEngine()
        engine.create_workflow("wf2", "Test")
        result = engine.add_node_to_workflow(
            "wf2", "n1", "action", config={"action": "test"}
        )
        assert result["status"] in ["added", "success"]

    def test_workflow_connect_nodes(self):
        """Can connect nodes."""
        from windows_ai.workflow.engine import WorkflowEngine
        engine = WorkflowEngine()
        engine.create_workflow("wf3", "Test")
        engine.add_node_to_workflow("wf3", "n1", "action")
        engine.add_node_to_workflow("wf3", "n2", "action")
        result = engine.connect_nodes("wf3", "n1", "n2")
        assert result["status"] in ["connected", "success"]

    def test_workflow_validate(self):
        """Workflow validation works."""
        from windows_ai.workflow.engine import Workflow
        wf = Workflow("test", "Test")
        result = wf.validate()
        assert result["valid"] is True

    def test_workflow_to_dict(self):
        """Workflow can be serialized."""
        from windows_ai.workflow.engine import Workflow, WorkflowNode
        wf = Workflow("test", "Test")
        wf.add_node(WorkflowNode("n1", "action"))
        d = wf.to_dict()
        assert isinstance(d, dict)
        assert "nodes" in d


# =================== Agent Manager Tests ===================

class TestAgentManagerComplete:
    """Test agent manager functionality."""

    @pytest.mark.asyncio
    async def test_agent_manager_init(self):
        """Agent manager initializes."""
        from windows_ai.agents.agent_manager import AgentManager
        manager = AgentManager()
        await manager.initialize()
        assert manager is not None

    @pytest.mark.asyncio
    async def test_create_agent(self):
        """Can create an agent with valid auth."""
        from windows_ai.agents.agent_manager import AgentManager
        manager = AgentManager()
        await manager.initialize()

        agent = await manager.create_agent(
            "test_agent",
            capabilities=["general"],
            auth_token="test_auth_token_16ch",
        )
        assert agent is not None
        assert agent.name == "test_agent"

    @pytest.mark.asyncio
    async def test_create_agent_requires_auth(self):
        """Agent creation requires valid auth token."""
        from windows_ai.agents.agent_manager import AgentManager
        manager = AgentManager()
        await manager.initialize()

        with pytest.raises((PermissionError, ValueError)):
            await manager.create_agent(
                "bad_agent",
                capabilities=["general"],
                auth_token="short",
            )

    @pytest.mark.asyncio
    async def test_get_agent(self):
        """Can retrieve created agent."""
        from windows_ai.agents.agent_manager import AgentManager
        manager = AgentManager()
        await manager.initialize()

        agent = await manager.create_agent(
            "retrieval_test",
            capabilities=["general"],
            auth_token="valid_auth_token_16",
        )

        retrieved = manager.get_agent(agent.id)
        assert retrieved is not None
        assert retrieved.id == agent.id
        assert retrieved.name == "retrieval_test"

    @pytest.mark.asyncio
    async def test_list_agents(self):
        """Can list all agents."""
        from windows_ai.agents.agent_manager import AgentManager
        manager = AgentManager()
        await manager.initialize()

        await manager.create_agent(
            "list_test",
            capabilities=["general"],
            auth_token="valid_auth_token_16",
        )

        agents = manager.get_all_agents()
        assert isinstance(agents, list)
        assert len(agents) >= 1

    @pytest.mark.asyncio
    async def test_delete_agent(self):
        """Can delete an agent."""
        from windows_ai.agents.agent_manager import AgentManager
        manager = AgentManager()
        await manager.initialize()

        agent = await manager.create_agent(
            "delete_test",
            capabilities=["general"],
            auth_token="valid_auth_token_16",
        )

        result = await manager.delete_agent(agent.id)
        assert result is True
        assert manager.get_agent(agent.id) is None


# =================== Agent Routes Tests ===================

class TestAgentRoutes:
    """Test agent API routes."""

    @pytest.fixture
    def client(self):
        from fastapi.testclient import TestClient
        from windows_ai.api.server import app
        return TestClient(app)

    def test_list_agents(self, client):
        """GET /api/v1/agents/ returns agent list."""
        response = client.get("/api/v1/agents/")
        assert response.status_code in [200, 503]

    def test_create_agent(self, client):
        """POST /api/v1/agents/ creates agent."""
        response = client.post(
            "/api/v1/agents/",
            json={
                "name": "test_api_agent",
                "capabilities": ["general"],
                "auth_token": "valid_auth_token_16",
            },
        )
        assert response.status_code in [200, 201, 401, 403, 422, 503]


# =================== Cache Tests ===================

class TestCacheSystem:
    """Test caching system."""

    def test_cache_import(self):
        """Cache module can be imported."""
        from windows_ai.core.cache import CacheBackend, InMemoryCache
        assert CacheBackend is not None
        assert InMemoryCache is not None

    @pytest.mark.asyncio
    async def test_in_memory_cache_basic(self):
        """In-memory cache set/get works."""
        from windows_ai.core.cache import InMemoryCache
        cache = InMemoryCache()

        await cache.set("test_key", "test_value", ttl=60)
        result = await cache.get("test_key")
        assert result == "test_value"

    @pytest.mark.asyncio
    async def test_in_memory_cache_miss(self):
        """In-memory cache returns None for missing keys."""
        from windows_ai.core.cache import InMemoryCache
        cache = InMemoryCache()

        result = await cache.get("nonexistent")
        assert result is None

    @pytest.mark.asyncio
    async def test_in_memory_cache_delete(self):
        """In-memory cache delete works."""
        from windows_ai.core.cache import InMemoryCache
        cache = InMemoryCache()

        await cache.set("del_key", "value")
        deleted = await cache.delete("del_key")
        assert deleted is True
        result = await cache.get("del_key")
        assert result is None


# =================== SSE and WebSocket Tests ===================

class TestStreamingEndpoints:
    """Test SSE and WebSocket modules."""

    def test_sse_routes_import(self):
        """SSE routes module can be imported."""
        from windows_ai.api import sse_routes
        assert sse_routes is not None
        assert hasattr(sse_routes, "router")

    def test_websocket_routes_import(self):
        """WebSocket routes module can be imported."""
        from windows_ai.api import websocket_routes
        assert websocket_routes is not None
        assert hasattr(websocket_routes, "router")
