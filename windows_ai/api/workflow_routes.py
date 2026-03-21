"""
Workflow API Routes

REST API endpoints for creating, managing, and executing workflows.
Wraps the WorkflowEngine with HTTP endpoints.
"""

from fastapi import APIRouter, HTTPException
from typing import Dict, Any, List, Optional
from pydantic import BaseModel, Field
import logging

from windows_ai.workflow.engine import WorkflowEngine

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/v1/workflows", tags=["workflows"])

# Global workflow engine instance
_engine: Optional[WorkflowEngine] = None


def get_engine() -> WorkflowEngine:
    """Get or create workflow engine."""
    global _engine
    if _engine is None:
        _engine = WorkflowEngine()
    return _engine


# --- Pydantic Models ---

class CreateWorkflowRequest(BaseModel):
    workflow_id: str = Field(..., description="Unique workflow identifier")
    name: str = Field(..., description="Human-readable workflow name")
    description: str = Field("", description="Workflow description")


class AddNodeRequest(BaseModel):
    node_id: str = Field(..., description="Unique node identifier")
    node_type: str = Field(..., description="Type of node (must have registered executor)")
    config: Dict[str, Any] = Field(default_factory=dict, description="Node configuration")
    inputs: Dict[str, Any] = Field(default_factory=dict, description="Initial inputs")


class ConnectNodesRequest(BaseModel):
    from_node: str = Field(..., description="Source node ID")
    to_node: str = Field(..., description="Target node ID")
    condition: Optional[str] = Field(None, description="Optional edge condition")
    data_mapping: Dict[str, str] = Field(
        default_factory=dict,
        description="Map source output keys to target input keys",
    )


class ExecuteWorkflowRequest(BaseModel):
    inputs: Dict[str, Any] = Field(default_factory=dict, description="Initial workflow inputs")


class ImportWorkflowRequest(BaseModel):
    workflow_id: str
    name: str
    description: str = ""
    nodes: Dict[str, Dict[str, Any]] = Field(default_factory=dict)
    edges: List[Dict[str, Any]] = Field(default_factory=list)
    metadata: Dict[str, Any] = Field(default_factory=dict)


# --- Endpoints ---

@router.post("/", summary="Create a new workflow")
async def create_workflow(request: CreateWorkflowRequest):
    """Create a new empty workflow."""
    engine = get_engine()
    result = engine.create_workflow(request.workflow_id, request.name)
    if result["status"] == "error":
        raise HTTPException(status_code=409, detail=result["message"])
    # Set optional description
    if request.description:
        engine.workflows[request.workflow_id].description = request.description
    return result


@router.get("/", summary="List all workflows")
async def list_workflows():
    """List all registered workflows."""
    engine = get_engine()
    return {
        "status": "success",
        "workflows": [
            wf.to_dict() for wf in engine.workflows.values()
        ],
    }


@router.get("/{workflow_id}", summary="Get workflow details")
async def get_workflow(workflow_id: str):
    """Get details of a specific workflow."""
    engine = get_engine()
    if workflow_id not in engine.workflows:
        raise HTTPException(status_code=404, detail=f"Workflow not found: {workflow_id}")
    return {
        "status": "success",
        "workflow": engine.workflows[workflow_id].to_dict(),
    }


@router.delete("/{workflow_id}", summary="Delete a workflow")
async def delete_workflow(workflow_id: str):
    """Delete a workflow."""
    engine = get_engine()
    if workflow_id not in engine.workflows:
        raise HTTPException(status_code=404, detail=f"Workflow not found: {workflow_id}")
    del engine.workflows[workflow_id]
    return {"status": "success", "message": f"Workflow '{workflow_id}' deleted"}


@router.post("/{workflow_id}/nodes", summary="Add a node to a workflow")
async def add_node(workflow_id: str, request: AddNodeRequest):
    """Add a node to an existing workflow."""
    engine = get_engine()
    result = engine.add_node_to_workflow(
        workflow_id, request.node_id, request.node_type,
        config=request.config, inputs=request.inputs,
    )
    if result["status"] == "error":
        raise HTTPException(status_code=400, detail=result["message"])
    return result


@router.post("/{workflow_id}/edges", summary="Connect two nodes")
async def connect_nodes(workflow_id: str, request: ConnectNodesRequest):
    """Connect two nodes with a directed edge."""
    engine = get_engine()
    result = engine.connect_nodes(
        workflow_id, request.from_node, request.to_node,
        condition=request.condition, data_mapping=request.data_mapping,
    )
    if result["status"] == "error":
        raise HTTPException(status_code=400, detail=result["message"])
    return result


@router.post("/{workflow_id}/validate", summary="Validate workflow structure")
async def validate_workflow(workflow_id: str):
    """Validate the workflow is a valid DAG with no missing references."""
    engine = get_engine()
    if workflow_id not in engine.workflows:
        raise HTTPException(status_code=404, detail=f"Workflow not found: {workflow_id}")
    return engine.workflows[workflow_id].validate()


@router.post("/{workflow_id}/execute", summary="Execute a workflow")
async def execute_workflow(workflow_id: str, request: ExecuteWorkflowRequest):
    """Execute a workflow and return results."""
    engine = get_engine()
    result = await engine.execute_workflow(workflow_id, request.inputs)
    if result["status"] == "error":
        code = 404 if "not found" in result.get("message", "").lower() else 400
        raise HTTPException(status_code=code, detail=result.get("message", "Execution failed"))
    return result


@router.get("/{workflow_id}/export", summary="Export workflow as JSON")
async def export_workflow(workflow_id: str):
    """Export a workflow definition as JSON."""
    engine = get_engine()
    result = engine.export_workflow(workflow_id)
    if result["status"] == "error":
        raise HTTPException(status_code=404, detail=result["message"])
    return result


@router.post("/import", summary="Import a workflow from JSON")
async def import_workflow(request: ImportWorkflowRequest):
    """Import a workflow from a JSON definition."""
    engine = get_engine()
    result = engine.import_workflow(request.model_dump())
    if result["status"] == "error":
        raise HTTPException(status_code=400, detail=result["message"])
    return result


@router.get("/executions/{execution_id}", summary="Get execution status")
async def get_execution_status(execution_id: str):
    """Get the status of a workflow execution."""
    engine = get_engine()
    result = engine.get_execution_status(execution_id)
    if result["status"] == "error":
        raise HTTPException(status_code=404, detail=result["message"])
    return result
