"""API routes for the canonical Windows-AI runtime.

This is the stable API boundary for the architecture described by
AI_BLUEPRINT.md. It exposes runtime capabilities, agents, tools, workspaces,
and direct tool execution without replacing the existing legacy routes.
"""
from __future__ import annotations

from typing import Any

from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel, Field


router = APIRouter(prefix="/api/v1/runtime", tags=["runtime"])


class WorkspaceRequest(BaseModel):
    root: str = Field(min_length=1)


class ChatRequest(BaseModel):
    agent_id: str = Field(default="windows-ai")
    message: str = Field(min_length=1)
    metadata: dict[str, Any] = Field(default_factory=dict)


class ToolRequest(BaseModel):
    tool_name: str = Field(min_length=1)
    arguments: dict[str, Any] = Field(default_factory=dict)
    actor: str = Field(default="api")
    approved: bool = False


def _runtime(request: Request):
    runtime = getattr(request.app.state, "canonical_runtime", None)
    if runtime is None:
        raise HTTPException(status_code=503, detail="Canonical runtime is not initialized")
    return runtime


@router.get("/capabilities")
async def capabilities(request: Request):
    return _runtime(request).capabilities()


@router.get("/tools")
async def tools(request: Request):
    runtime = _runtime(request)
    return {"tools": runtime.core.tools.discover()}


@router.get("/agents")
async def agents(request: Request):
    runtime = _runtime(request)
    return {"agents": runtime.core.agents.describe()}


@router.post("/workspace")
async def open_workspace(payload: WorkspaceRequest, request: Request):
    runtime = _runtime(request)
    try:
        workspace = runtime.open_workspace(payload.root)
    except (OSError, ValueError) as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return {"id": workspace.id, "name": workspace.name, "root": str(workspace.root)}


@router.post("/chat")
async def chat(payload: ChatRequest, request: Request):
    runtime = _runtime(request)
    try:
        result = await runtime.chat(
            agent_id=payload.agent_id,
            message=payload.message,
            metadata=payload.metadata,
        )
    except (KeyError, ValueError) as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return result


@router.post("/tools/execute")
async def execute_tool(payload: ToolRequest, request: Request):
    runtime = _runtime(request)
    try:
        result = await runtime.execute_tool(
            tool_name=payload.tool_name,
            arguments=payload.arguments,
            actor=payload.actor,
            approved=payload.approved,
        )
    except PermissionError as exc:
        raise HTTPException(status_code=403, detail=str(exc)) from exc
    except (KeyError, ValueError) as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return result
