"""Agent Manager for orchestrating multiple agents"""

from typing import Dict, List, Optional, Any
import asyncio
import logging
from datetime import datetime
import uuid

from windows_ai.agents.agent import Agent, AgentStatus
from windows_ai.agents.task import Task, TaskStatus, TaskPriority
from windows_ai.core.plugin_manager import PluginManager

logger = logging.getLogger(__name__)

class AgentManager:
    """Manages multiple agents and task distribution"""

    def __init__(self, plugin_manager: PluginManager):
        self.plugin_manager = plugin_manager
        self.agents: Dict[str, Agent] = {}
        self.tasks: Dict[str, Task] = {}
        self.task_queue: List[Task] = []
        self.running = False
        self.created_at = datetime.utcnow()

    async def initialize(self):
        """Initialize the agent manager"""
        logger.info("Initializing agent manager...")

        # Create default general-purpose agent
        default_agent = await self.create_agent(
            name="Default Agent",
            plugins=[],  # Has access to all plugins
            config={'type': 'general'}
        )

        logger.info(f"Agent manager initialized with agent: {default_agent.id}")

    async def create_agent(
        self,
        name: str,
        plugins: Optional[List[str]] = None,
        config: Optional[Dict[str, Any]] = None
    ) -> Agent:
        """Create a new agent"""
        agent_id = f"agent_{uuid.uuid4().hex[:8]}"

        agent = Agent(
            agent_id=agent_id,
            name=name,
            plugin_manager=self.plugin_manager,
            plugins=plugins or [],
            config=config or {}
        )

        self.agents[agent_id] = agent
        logger.info(f"Created agent: {name} ({agent_id})")

        return agent

    async def delete_agent(self, agent_id: str) -> bool:
        """Delete an agent"""
        if agent_id not in self.agents:
            return False

        agent = self.agents[agent_id]

        # Can't delete if agent is busy
        if agent.status == AgentStatus.BUSY:
            logger.warning(f"Cannot delete busy agent: {agent_id}")
            return False

        del self.agents[agent_id]
        logger.info(f"Deleted agent: {agent_id}")

        return True

    async def create_task(
        self,
        description: str,
        parameters: Optional[Dict[str, Any]] = None,
        required_plugins: Optional[List[str]] = None,
        priority: TaskPriority = TaskPriority.NORMAL
    ) -> Task:
        """Create a new task"""
        task = Task(
            description=description,
            parameters=parameters or {},
            required_plugins=required_plugins or [],
            priority=priority
        )

        self.tasks[task.id] = task
        self.task_queue.append(task)

        # Sort queue by priority
        self.task_queue.sort(key=lambda t: t.priority.value, reverse=True)

        logger.info(f"Created task: {task.description} ({task.id})")

        return task

    async def execute_task(self, task_id: str) -> Dict[str, Any]:
        """Execute a specific task"""
        if task_id not in self.tasks:
            return {'success': False, 'error': 'Task not found'}

        task = self.tasks[task_id]

        # Find suitable agent
        agent = self._find_suitable_agent(task)

        if not agent:
            return {'success': False, 'error': 'No suitable agent available'}

        # Execute task
        result = await agent.execute_task(task)

        return result

    async def execute_task_description(
        self,
        description: str,
        parameters: Optional[Dict[str, Any]] = None,
        required_plugins: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """Create and execute a task from description"""
        task = await self.create_task(
            description=description,
            parameters=parameters,
            required_plugins=required_plugins
        )

        result = await self.execute_task(task.id)

        return result

    def _find_suitable_agent(self, task: Task) -> Optional[Agent]:
        """Find the most suitable agent for a task"""
        # Find idle agents
        idle_agents = [
            agent for agent in self.agents.values()
            if agent.status == AgentStatus.IDLE
        ]

        if not idle_agents:
            logger.warning("No idle agents available")
            return None

        # If task requires specific plugins, find agent with those plugins
        if task.required_plugins:
            for agent in idle_agents:
                if all(p in agent.plugins or not agent.plugins for p in task.required_plugins):
                    return agent

        # Return first idle agent (default)
        return idle_agents[0]

    async def process_task_queue(self):
        """Process queued tasks"""
        while self.task_queue:
            task = self.task_queue[0]

            # Check dependencies
            if task.dependencies:
                deps_complete = all(
                    self.tasks[dep_id].status == TaskStatus.COMPLETED
                    for dep_id in task.dependencies
                    if dep_id in self.tasks
                )

                if not deps_complete:
                    # Move to end of queue
                    self.task_queue.append(self.task_queue.pop(0))
                    continue

            # Execute task
            await self.execute_task(task.id)

            # Remove from queue
            self.task_queue.pop(0)

    def get_agent(self, agent_id: str) -> Optional[Agent]:
        """Get an agent by ID"""
        return self.agents.get(agent_id)

    def get_all_agents(self) -> List[Dict[str, Any]]:
        """Get all agents"""
        return [agent.to_dict() for agent in self.agents.values()]

    def get_task(self, task_id: str) -> Optional[Task]:
        """Get a task by ID"""
        return self.tasks.get(task_id)

    def get_all_tasks(self) -> List[Dict[str, Any]]:
        """Get all tasks"""
        return [task.to_dict() for task in self.tasks.values()]

    def get_stats(self) -> Dict[str, Any]:
        """Get manager statistics"""
        total_tasks = len(self.tasks)
        completed = sum(1 for t in self.tasks.values() if t.status == TaskStatus.COMPLETED)
        failed = sum(1 for t in self.tasks.values() if t.status == TaskStatus.FAILED)
        pending = sum(1 for t in self.tasks.values() if t.status == TaskStatus.PENDING)
        in_progress = sum(1 for t in self.tasks.values() if t.status == TaskStatus.IN_PROGRESS)

        return {
            'agents': {
                'total': len(self.agents),
                'idle': sum(1 for a in self.agents.values() if a.status == AgentStatus.IDLE),
                'busy': sum(1 for a in self.agents.values() if a.status == AgentStatus.BUSY),
            },
            'tasks': {
                'total': total_tasks,
                'completed': completed,
                'failed': failed,
                'pending': pending,
                'in_progress': in_progress,
                'queued': len(self.task_queue)
            },
            'created_at': self.created_at.isoformat()
        }

    async def shutdown(self):
        """Shutdown the agent manager"""
        logger.info("Shutting down agent manager...")

        # Wait for busy agents to finish
        busy_agents = [a for a in self.agents.values() if a.status == AgentStatus.BUSY]

        if busy_agents:
            logger.info(f"Waiting for {len(busy_agents)} busy agents...")
            # In production, implement proper timeout and cancellation

        self.agents.clear()
        self.tasks.clear()
        self.task_queue.clear()

        logger.info("Agent manager shutdown complete")
