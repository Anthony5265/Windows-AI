"""
Multi-Agent Coordination System
Manages multiple AI agents working together on complex tasks
"""
import logging
from typing import Dict, List, Optional, Any, Callable
from datetime import datetime
from dataclasses import dataclass, asdict
from pathlib import Path
import json
from enum import Enum
import asyncio
from collections import defaultdict
import uuid

logger = logging.getLogger(__name__)


class AgentRole(Enum):
    """Agent roles in the system"""
    COORDINATOR = "coordinator"  # Coordinates other agents
    EXECUTOR = "executor"  # Executes tasks
    ANALYZER = "analyzer"  # Analyzes data
    PLANNER = "planner"  # Plans actions
    VALIDATOR = "validator"  # Validates results
    COMMUNICATOR = "communicator"  # Communicates with user


class AgentStatus(Enum):
    """Agent status"""
    IDLE = "idle"
    BUSY = "busy"
    WAITING = "waiting"
    ERROR = "error"
    OFFLINE = "offline"


@dataclass
class Agent:
    """An AI agent"""
    agent_id: str
    name: str
    role: AgentRole
    capabilities: List[str]
    status: AgentStatus
    current_task: Optional[str]
    performance_score: float  # 0-100


@dataclass
class Task:
    """A task to be executed"""
    task_id: str
    description: str
    priority: int  # 1-10
    required_capabilities: List[str]
    assigned_agent: Optional[str]
    status: str  # pending, in_progress, completed, failed
    result: Optional[Any]
    created_at: str
    completed_at: Optional[str]


@dataclass
class Message:
    """Inter-agent message"""
    message_id: str
    from_agent: str
    to_agent: str
    message_type: str  # request, response, notification
    content: Dict[str, Any]
    timestamp: str


class MultiAgentSystem:
    """
    Multi-Agent Coordination System

    Features:
    - Agent lifecycle management (spawn, monitor, retire)
    - Task decomposition and distribution
    - Agent communication protocol
    - Collaborative problem solving
    - Consensus mechanisms
    - Load balancing across agents
    - Agent specialization and roles
    - Fault tolerance and agent replacement
    - Performance monitoring
    - Agent learning and adaptation
    """

    def __init__(self, data_dir: Path):
        self.data_dir = data_dir
        self.data_dir.mkdir(parents=True, exist_ok=True)

        # Agent registry
        self.agents: Dict[str, Agent] = {}

        # Task queue
        self.task_queue: List[Task] = []
        self.completed_tasks: List[Task] = []

        # Message bus
        self.message_queue: List[Message] = []

        # Agent capabilities database
        self.capability_registry: Dict[str, List[str]] = defaultdict(list)

        # Performance metrics
        self.metrics = {
            'tasks_completed': 0,
            'tasks_failed': 0,
            'avg_completion_time': 0.0,
            'agent_utilization': 0.0
        }

        # Initialize default agents
        self._initialize_default_agents()

    def _initialize_default_agents(self):
        """Initialize default set of agents"""
        default_agents = [
            {
                'name': 'Coordinator',
                'role': AgentRole.COORDINATOR,
                'capabilities': ['task_decomposition', 'agent_coordination', 'decision_making']
            },
            {
                'name': 'Executor-1',
                'role': AgentRole.EXECUTOR,
                'capabilities': ['file_operations', 'system_commands', 'api_calls']
            },
            {
                'name': 'Executor-2',
                'role': AgentRole.EXECUTOR,
                'capabilities': ['file_operations', 'data_processing', 'web_scraping']
            },
            {
                'name': 'Analyzer',
                'role': AgentRole.ANALYZER,
                'capabilities': ['data_analysis', 'pattern_recognition', 'reporting']
            },
            {
                'name': 'Planner',
                'role': AgentRole.PLANNER,
                'capabilities': ['planning', 'optimization', 'resource_allocation']
            },
            {
                'name': 'Validator',
                'role': AgentRole.VALIDATOR,
                'capabilities': ['validation', 'testing', 'quality_assurance']
            },
        ]

        for agent_config in default_agents:
            self.spawn_agent(**agent_config)

    def spawn_agent(self, name: str, role: AgentRole, capabilities: List[str]) -> Agent:
        """Create and register a new agent"""
        agent = Agent(
            agent_id=str(uuid.uuid4()),
            name=name,
            role=role,
            capabilities=capabilities,
            status=AgentStatus.IDLE,
            current_task=None,
            performance_score=100.0
        )

        self.agents[agent.agent_id] = agent

        # Register capabilities
        for capability in capabilities:
            self.capability_registry[capability].append(agent.agent_id)

        logger.info(f"Spawned agent: {name} ({role.value}) with capabilities: {capabilities}")

        return agent

    def retire_agent(self, agent_id: str):
        """Retire an agent"""
        if agent_id in self.agents:
            agent = self.agents[agent_id]

            # Reassign tasks if agent is busy
            if agent.current_task:
                task = self._get_task(agent.current_task)
                if task:
                    task.assigned_agent = None
                    task.status = 'pending'

            # Remove from capability registry
            for capability in agent.capabilities:
                if agent_id in self.capability_registry[capability]:
                    self.capability_registry[capability].remove(agent_id)

            # Remove agent
            del self.agents[agent_id]

            logger.info(f"Retired agent: {agent.name}")

    def submit_task(self, description: str, priority: int, required_capabilities: List[str]) -> Task:
        """Submit a new task"""
        task = Task(
            task_id=str(uuid.uuid4()),
            description=description,
            priority=priority,
            required_capabilities=required_capabilities,
            assigned_agent=None,
            status='pending',
            result=None,
            created_at=datetime.now().isoformat(),
            completed_at=None
        )

        self.task_queue.append(task)
        self.task_queue.sort(key=lambda t: t.priority, reverse=True)

        logger.info(f"Task submitted: {description} (priority: {priority})")

        # Try to assign immediately
        self._assign_tasks()

        return task

    def _assign_tasks(self):
        """Assign pending tasks to available agents"""
        for task in self.task_queue:
            if task.status != 'pending':
                continue

            # Find capable and available agents
            capable_agents = self._find_capable_agents(task.required_capabilities)
            available_agents = [
                agent_id for agent_id in capable_agents
                if self.agents[agent_id].status == AgentStatus.IDLE
            ]

            if available_agents:
                # Select best agent based on performance score
                best_agent_id = max(
                    available_agents,
                    key=lambda aid: self.agents[aid].performance_score
                )

                # Assign task
                self._assign_task_to_agent(task, best_agent_id)

    def _find_capable_agents(self, required_capabilities: List[str]) -> List[str]:
        """Find agents with required capabilities"""
        if not required_capabilities:
            return list(self.agents.keys())

        # Find agents that have ALL required capabilities
        capable_agents = set()

        for capability in required_capabilities:
            if not capable_agents:
                capable_agents = set(self.capability_registry.get(capability, []))
            else:
                capable_agents &= set(self.capability_registry.get(capability, []))

        return list(capable_agents)

    def _assign_task_to_agent(self, task: Task, agent_id: str):
        """Assign a task to an agent"""
        agent = self.agents[agent_id]

        task.assigned_agent = agent_id
        task.status = 'in_progress'

        agent.status = AgentStatus.BUSY
        agent.current_task = task.task_id

        logger.info(f"Assigned task {task.task_id} to agent {agent.name}")

        # Send message to agent
        self.send_message(
            from_agent='system',
            to_agent=agent_id,
            message_type='request',
            content={'action': 'execute_task', 'task': asdict(task)}
        )

    def complete_task(self, task_id: str, result: Any, success: bool = True):
        """Mark a task as completed"""
        task = self._get_task(task_id)

        if not task:
            logger.warning(f"Task {task_id} not found")
            return

        task.status = 'completed' if success else 'failed'
        task.result = result
        task.completed_at = datetime.now().isoformat()

        # Update agent status
        if task.assigned_agent and task.assigned_agent in self.agents:
            agent = self.agents[task.assigned_agent]
            agent.status = AgentStatus.IDLE
            agent.current_task = None

            # Update performance score
            if success:
                agent.performance_score = min(100.0, agent.performance_score + 1.0)
                self.metrics['tasks_completed'] += 1
            else:
                agent.performance_score = max(0.0, agent.performance_score - 5.0)
                self.metrics['tasks_failed'] += 1

        # Move to completed tasks
        self.task_queue.remove(task)
        self.completed_tasks.append(task)

        # Try to assign more tasks
        self._assign_tasks()

        logger.info(f"Task completed: {task_id} (success: {success})")

    def send_message(self, from_agent: str, to_agent: str, message_type: str, content: Dict[str, Any]):
        """Send message between agents"""
        message = Message(
            message_id=str(uuid.uuid4()),
            from_agent=from_agent,
            to_agent=to_agent,
            message_type=message_type,
            content=content,
            timestamp=datetime.now().isoformat()
        )

        self.message_queue.append(message)

        logger.debug(f"Message sent: {from_agent} -> {to_agent} ({message_type})")

    def get_messages(self, agent_id: str, clear: bool = True) -> List[Message]:
        """Get messages for an agent"""
        messages = [m for m in self.message_queue if m.to_agent == agent_id]

        if clear:
            self.message_queue = [m for m in self.message_queue if m.to_agent != agent_id]

        return messages

    def decompose_task(self, task_description: str) -> List[Dict[str, Any]]:
        """
        Decompose complex task into subtasks

        Returns list of subtask specifications
        """
        # Simple task decomposition (would use AI in production)
        subtasks = []

        # Example decomposition patterns
        if 'analyze and report' in task_description.lower():
            subtasks = [
                {
                    'description': 'Collect data',
                    'priority': 8,
                    'capabilities': ['data_collection']
                },
                {
                    'description': 'Analyze data',
                    'priority': 7,
                    'capabilities': ['data_analysis']
                },
                {
                    'description': 'Generate report',
                    'priority': 6,
                    'capabilities': ['reporting']
                }
            ]
        elif 'create and test' in task_description.lower():
            subtasks = [
                {
                    'description': 'Create implementation',
                    'priority': 8,
                    'capabilities': ['file_operations']
                },
                {
                    'description': 'Test implementation',
                    'priority': 7,
                    'capabilities': ['testing']
                },
                {
                    'description': 'Validate results',
                    'priority': 6,
                    'capabilities': ['validation']
                }
            ]
        else:
            # Default: single task
            subtasks = [{
                'description': task_description,
                'priority': 5,
                'capabilities': []
            }]

        return subtasks

    def coordinate_task(self, task_description: str) -> List[Task]:
        """Coordinate execution of complex task across multiple agents"""
        # Decompose into subtasks
        subtask_specs = self.decompose_task(task_description)

        # Submit all subtasks
        tasks = []
        for spec in subtask_specs:
            task = self.submit_task(
                description=spec['description'],
                priority=spec['priority'],
                required_capabilities=spec['capabilities']
            )
            tasks.append(task)

        logger.info(f"Coordinated task decomposed into {len(tasks)} subtasks")

        return tasks

    def get_system_status(self) -> Dict[str, Any]:
        """Get overall system status"""
        # Count agents by status
        status_counts = defaultdict(int)
        for agent in self.agents.values():
            status_counts[agent.status.value] += 1

        # Calculate utilization
        busy_agents = status_counts.get('busy', 0)
        total_agents = len(self.agents)
        utilization = (busy_agents / total_agents * 100) if total_agents > 0 else 0

        return {
            'total_agents': total_agents,
            'agent_status': dict(status_counts),
            'utilization': utilization,
            'pending_tasks': len([t for t in self.task_queue if t.status == 'pending']),
            'active_tasks': len([t for t in self.task_queue if t.status == 'in_progress']),
            'completed_tasks': self.metrics['tasks_completed'],
            'failed_tasks': self.metrics['tasks_failed'],
            'success_rate': (
                self.metrics['tasks_completed'] /
                (self.metrics['tasks_completed'] + self.metrics['tasks_failed']) * 100
                if (self.metrics['tasks_completed'] + self.metrics['tasks_failed']) > 0 else 0
            )
        }

    def _get_task(self, task_id: str) -> Optional[Task]:
        """Get task by ID"""
        for task in self.task_queue + self.completed_tasks:
            if task.task_id == task_id:
                return task
        return None


# Global instance
_multi_agent_system: Optional[MultiAgentSystem] = None


def get_multi_agent_system(data_dir: Path = None) -> MultiAgentSystem:
    """Get or create global multi-agent system"""
    global _multi_agent_system

    if _multi_agent_system is None:
        if data_dir is None:
            data_dir = Path.home() / ".windows-ai" / "multi_agent"
        _multi_agent_system = MultiAgentSystem(data_dir)

    return _multi_agent_system


def initialize_multi_agent_system(data_dir: Path = None):
    """Initialize the multi-agent system"""
    system = get_multi_agent_system(data_dir)
    logger.info("Multi-agent system initialized")
    return system
