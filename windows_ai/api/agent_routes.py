"""Agent API Routes - Complete agent orchestration endpoints"""

from fastapi import APIRouter, HTTPException, Depends, BackgroundTasks, Query
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field
from datetime import datetime
import logging
import asyncio

from windows_ai.agents.agent_manager import AgentManager
from windows_ai.agents.agent import AgentStatus
from windows_ai.agents.task import TaskStatus, TaskPriority
from windows_ai.api.auth import get_current_user
from windows_ai.api.rate_limiter import standard_rate_limiter

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/v1/agents", tags=["agents"])

_agent_manager: Optional[AgentManager] = None


def get_agent_manager() -> AgentManager:
    """Get or create agent manager"""
    global _agent_manager
    if _agent_manager is None:
        raise HTTPException(status_code=503, detail="Agent manager not initialized")
    return _agent_manager


def set_agent_manager(manager: AgentManager):
    """Set agent manager instance"""
    global _agent_manager
    _agent_manager = manager


class AgentCreateRequest(BaseModel):
    """Request to create a new agent"""
    name: str = Field(..., description="Agent name", min_length=1, max_length=100)
    capabilities: Optional[List[str]] = Field(default=None, description="Agent capabilities/plugins")
    config: Optional[Dict[str, Any]] = Field(default=None, description="Agent configuration")
    auth_token: Optional[str] = Field(default=None, description="Authentication token for the agent")


class AgentResponse(BaseModel):
    id: str
    name: str
    status: str
    capabilities: List[str]
    created_at: str
    tasks_completed: int
    current_task: Optional[str] = None


class TaskCreateRequest(BaseModel):
    description: str = Field(..., description="Task description")
    parameters: Optional[Dict[str, Any]] = Field(default=None, description="Task parameters")
    required_plugins: Optional[List[str]] = Field(default=None, description="Required plugins")
    priority: Optional[str] = Field(default="normal", description="Task priority: low, normal, high")
    agent_id: Optional[str] = Field(default=None, description="Specific agent to assign to")


class TaskResponse(BaseModel):
    id: str
    description: str
    status: str
    priority: str
    created_at: str
    assigned_agent: Optional[str] = None
    result: Optional[Dict[str, Any]] = None
    error: Optional[str] = None


class AgentStatsResponse(BaseModel):
    total_agents: int
    idle_agents: int
    busy_agents: int
    total_tasks: int
    completed_tasks: int
    failed_tasks: int
    pending_tasks: int
    in_progress_tasks: int


class MultiAgentWorkflowRequest(BaseModel):
    name: str = Field(..., description="Workflow name")
    tasks: List[Dict[str, Any]] = Field(..., description="List of tasks with dependencies")
    agents: Optional[List[str]] = Field(default=None, description="Specific agents to use")
    parallel: bool = Field(default=False, description="Execute tasks in parallel")


@router.post("/", response_model=AgentResponse, dependencies=[Depends(standard_rate_limiter)])
async def create_agent(request: AgentCreateRequest, user=Depends(get_current_user), manager: AgentManager = Depends(get_agent_manager)):
    try:
        agent = await manager.create_agent(name=request.name, capabilities=request.capabilities, config=request.config, auth_token=request.auth_token)
        return AgentResponse(id=agent.id, name=agent.name, status=agent.status.value, capabilities=agent.capabilities, created_at=agent.created_at.isoformat(), tasks_completed=len(agent.task_history))
    except PermissionError as e:
        raise HTTPException(status_code=403, detail=str(e))
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Failed to create agent: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to create agent: {str(e)}")


@router.get("/", response_model=List[AgentResponse])
async def list_agents(status: Optional[str] = Query(None, description="Filter by status"), user=Depends(get_current_user), manager: AgentManager = Depends(get_agent_manager)):
    try:
        agents = manager.get_all_agents()
        if status:
            agents = [a for a in agents if a.get('status', '').lower() == status.lower()]
        return [AgentResponse(id=a['id'], name=a['name'], status=a['status'], capabilities=a.get('capabilities', []), created_at=a.get('created_at', datetime.utcnow().isoformat()), tasks_completed=a.get('tasks_completed', 0), current_task=a.get('current_task')) for a in agents]
    except Exception as e:
        logger.error(f"Failed to list agents: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{agent_id}", response_model=AgentResponse)
async def get_agent(agent_id: str, user=Depends(get_current_user), manager: AgentManager = Depends(get_agent_manager)):
    agent = manager.get_agent(agent_id)
    if not agent:
        raise HTTPException(status_code=404, detail=f"Agent {agent_id} not found")
    agent_dict = agent.to_dict()
    return AgentResponse(id=agent_dict['id'], name=agent_dict['name'], status=agent_dict['status'], capabilities=agent_dict.get('capabilities', []), created_at=agent_dict.get('created_at', datetime.utcnow().isoformat()), tasks_completed=agent_dict.get('tasks_completed', 0), current_task=agent_dict.get('current_task'))


@router.delete("/{agent_id}")
async def delete_agent(agent_id: str, user=Depends(get_current_user), manager: AgentManager = Depends(get_agent_manager)):
    success = await manager.delete_agent(agent_id)
    if not success:
        raise HTTPException(status_code=400, detail=f"Cannot delete agent {agent_id} (not found or busy)")
    return {"success": True, "message": f"Agent {agent_id} deleted"}


@router.get("/{agent_id}/tasks", response_model=List[TaskResponse])
async def get_agent_tasks(agent_id: str, user=Depends(get_current_user), manager: AgentManager = Depends(get_agent_manager)):
    agent = manager.get_agent(agent_id)
    if not agent:
        raise HTTPException(status_code=404, detail=f"Agent {agent_id} not found")
    all_tasks = manager.get_all_tasks()
    agent_tasks = [t for t in all_tasks if t.get('assigned_agent') == agent_id]
    return [TaskResponse(id=t['id'], description=t['description'], status=t['status'], priority=t.get('priority', 'normal'), created_at=t.get('created_at', datetime.utcnow().isoformat()), assigned_agent=t.get('assigned_agent'), result=t.get('result'), error=t.get('error')) for t in agent_tasks]


@router.post("/tasks", response_model=TaskResponse, dependencies=[Depends(standard_rate_limiter)])
async def create_task(request: TaskCreateRequest, background_tasks: BackgroundTasks, user=Depends(get_current_user), manager: AgentManager = Depends(get_agent_manager)):
    try:
        priority_map = {'low': TaskPriority.LOW, 'normal': TaskPriority.NORMAL, 'high': TaskPriority.HIGH}
        priority = priority_map.get(request.priority.lower(), TaskPriority.NORMAL)
        task = await manager.create_task(task_or_dict=request.description, parameters=request.parameters, required_plugins=request.required_plugins, priority=priority)
        if request.agent_id:
            agent = await manager.assign_task(task, request.agent_id)
            if not agent:
                logger.warning(f"Could not assign task {task.id} to agent {request.agent_id}")
        background_tasks.add_task(manager.execute_task, task.id)
        return TaskResponse(id=task.id, description=task.description, status=task.status.value, priority=task.priority.value, created_at=task.created_at.isoformat(), assigned_agent=task.assigned_agent)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Failed to create task: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/tasks", response_model=List[TaskResponse])
async def list_tasks(status: Optional[str] = Query(None, description="Filter by status"), agent_id: Optional[str] = Query(None, description="Filter by agent"), user=Depends(get_current_user), manager: AgentManager = Depends(get_agent_manager)):
    tasks = manager.get_all_tasks()
    if status:
        tasks = [t for t in tasks if t.get('status', '').lower() == status.lower()]
    if agent_id:
        tasks = [t for t in tasks if t.get('assigned_agent') == agent_id]
    return [TaskResponse(id=t['id'], description=t['description'], status=t['status'], priority=t.get('priority', 'normal'), created_at=t.get('created_at', datetime.utcnow().isoformat()), assigned_agent=t.get('assigned_agent'), result=t.get('result'), error=t.get('error')) for t in tasks]


@router.get("/tasks/{task_id}", response_model=TaskResponse)
async def get_task(task_id: str, user=Depends(get_current_user), manager: AgentManager = Depends(get_agent_manager)):
    task = manager.get_task(task_id)
    if not task:
        raise HTTPException(status_code=404, detail=f"Task {task_id} not found")
    task_dict = task.to_dict()
    return TaskResponse(id=task_dict['id'], description=task_dict['description'], status=task_dict['status'], priority=task_dict.get('priority', 'normal'), created_at=task_dict.get('created_at', datetime.utcnow().isoformat()), assigned_agent=task_dict.get('assigned_agent'), result=task_dict.get('result'), error=task_dict.get('error'))


@router.post("/tasks/{task_id}/execute")
async def execute_task(task_id: str, background_tasks: BackgroundTasks, user=Depends(get_current_user), manager: AgentManager = Depends(get_agent_manager)):
    task = manager.get_task(task_id)
    if not task:
        raise HTTPException(status_code=404, detail=f"Task {task_id} not found")
    if task.status != TaskStatus.PENDING:
        raise HTTPException(status_code=400, detail=f"Task {task_id} is not pending (status: {task.status.value})")
    background_tasks.add_task(manager.execute_task, task_id)
    return {"success": True, "message": f"Task {task_id} execution started"}


@router.post("/workflows", dependencies=[Depends(standard_rate_limiter)])
async def create_workflow(request: MultiAgentWorkflowRequest, background_tasks: BackgroundTasks, user=Depends(get_current_user), manager: AgentManager = Depends(get_agent_manager)):
    try:
        workflow_id = f"workflow_{datetime.utcnow().strftime('%Y%m%d%H%M%S')}"
        task_ids = []
        for task_spec in request.tasks:
            task = await manager.create_task(task_or_dict=task_spec.get('description', ''), parameters=task_spec.get('parameters'), required_plugins=task_spec.get('required_plugins'))
            task_ids.append(task.id)
        if request.parallel:
            async def execute_parallel():
                await asyncio.gather(*[manager.execute_task(tid) for tid in task_ids])
            background_tasks.add_task(execute_parallel)
        else:
            async def execute_sequential():
                for tid in task_ids:
                    await manager.execute_task(tid)
            background_tasks.add_task(execute_sequential)
        return {"workflow_id": workflow_id, "task_ids": task_ids, "mode": "parallel" if request.parallel else "sequential", "status": "started"}
    except Exception as e:
        logger.error(f"Failed to create workflow: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/stats", response_model=AgentStatsResponse)
async def get_stats(user=Depends(get_current_user), manager: AgentManager = Depends(get_agent_manager)):
    stats = manager.get_stats()
    return AgentStatsResponse(total_agents=stats['agents']['total'], idle_agents=stats['agents']['idle'], busy_agents=stats['agents']['busy'], total_tasks=stats['tasks']['total'], completed_tasks=stats['tasks']['completed'], failed_tasks=stats['tasks']['failed'], pending_tasks=stats['tasks']['pending'], in_progress_tasks=stats['tasks']['in_progress'])
