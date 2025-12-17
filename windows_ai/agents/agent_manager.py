"""Agent Manager for orchestrating multiple agents"""

from typing import Dict, List, Optional, Any, Union
import asyncio
import logging
from datetime import datetime
import uuid
import re

from windows_ai.agents.agent import Agent, AgentStatus
from windows_ai.agents.task import Task, TaskStatus, TaskPriority
from windows_ai.core.plugin_manager import PluginManager
from windows_ai.exceptions import SecurityError, ResourceError, ValidationError

logger = logging.getLogger(__name__)

# Constants for resource limits
MAX_TASK_QUEUE_SIZE = 1000
MAX_TASK_DESCRIPTION_LENGTH = 10000
ALLOWED_TASK_TYPES = {
    "test", "query", "analysis", "process", "transform", "execute_command"
}
DANGEROUS_COMMANDS = [
    "rm", "del", "format", "shutdown", "reboot", "kill", "pkill",
    "dd", "mkfs", "/", "\\", "*"
]
DANGEROUS_TASK_TYPES = {
    "elevate_privileges", "sudo", "runas", "admin_access"
}

class AgentManager:
    """Manages multiple agents and task distribution"""

    def __init__(self, plugin_manager: Optional[PluginManager] = None):
        self.plugin_manager = plugin_manager
        self.agents: Dict[str, Agent] = {}
        self.tasks: Dict[str, Task] = {}
        self.task_queue: List[Task] = []
        self.running = False
        self.created_at = datetime.utcnow()

    async def initialize(self):
        """Initialize the agent manager"""
        import os
        logger.info("Initializing agent manager...")

        # Create default general-purpose agent with system auth token
        system_token = os.environ.get('AGENT_AUTH_TOKEN', 'system-default-token-' + uuid.uuid4().hex[:16])
        default_agent = await self.create_agent(
            name="Default Agent",
            plugins=[],  # Has access to all plugins
            config={'type': 'general'},
            auth_token=system_token
        )

        logger.info(f"Agent manager initialized with agent: {default_agent.id}")

    async def create_agent(
        self,
        name: str,
        plugins: Optional[List[str]] = None,
        config: Optional[Dict[str, Any]] = None,
        capabilities: Optional[List[str]] = None,
        available_plugins: Optional[List[str]] = None,
        auth_token: Optional[str] = None
    ) -> Agent:
        """Create a new agent with authentication"""
        import os
        
        # Require authentication (from parameter, config, or environment)
        token = auth_token or (config or {}).get('auth_token') or os.environ.get('AGENT_AUTH_TOKEN')
        if not token:
            raise PermissionError("Authentication required: AGENT_AUTH_TOKEN must be provided")
        
        # Validate token (basic validation - in production use JWT/OAuth)
        if len(token) < 16:
            raise ValueError("Invalid authentication token: must be at least 16 characters")
        
        agent_id = f"agent_{uuid.uuid4().hex[:8]}"
        
        # Determine capabilities
        agent_capabilities = plugins or capabilities or available_plugins or []
        
        # Create agent with auth token
        final_config = config.copy() if config else {}
        final_config['auth_token'] = token
        final_config['capabilities'] = agent_capabilities
        
        agent = Agent(
            name=name,
            agent_id=agent_id,
            plugin_manager=self.plugin_manager,
            plugins=agent_capabilities,
            config=final_config
        )

        self.agents[agent_id] = agent
        logger.info(f"Agent created: {name} ({agent_id}) with capabilities: {agent_capabilities}")

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
        task_or_dict: Union[str, Dict[str, Any]],
        parameters: Optional[Dict[str, Any]] = None,
        required_plugins: Optional[List[str]] = None,
        priority: TaskPriority = TaskPriority.NORMAL
    ) -> Task:
        """Create a new task with validation.
        
        Args:
            task_or_dict: Either a task description string or a task dict
            parameters: Task parameters (when task_or_dict is string)
            required_plugins: Required plugins (when task_or_dict is string)
            priority: Task priority
            
        Returns:
            Created Task object
            
        Raises:
            ValueError: Invalid task structure or parameters
            TypeError: Invalid parameter types
            KeyError: Missing required fields
            SecurityError: Dangerous/malicious task detected
            ResourceError: Resource limits exceeded
        """
        # Check task queue size limit
        if len(self.task_queue) >= MAX_TASK_QUEUE_SIZE:
            raise ResourceError(
                f"Task queue limit exceeded: {len(self.task_queue)} >= {MAX_TASK_QUEUE_SIZE}"
            )
        
        # Handle dict-based task creation (new security-aware format)
        if isinstance(task_or_dict, dict):
            return await self._create_task_from_dict(task_or_dict)
        
        # Handle string description (legacy format)
        description = task_or_dict
        
        # Validate description
        if not description or not isinstance(description, str):
            raise ValueError("Task description must be a non-empty string")
        
        if len(description) > MAX_TASK_DESCRIPTION_LENGTH:
            raise ValueError(
                f"Task description too long: {len(description)} > {MAX_TASK_DESCRIPTION_LENGTH}"
            )
        
        # Create task
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
    
    async def _create_task_from_dict(self, task_dict: Dict[str, Any]) -> Task:
        """Create task from dictionary with security validation.
        
        Args:
            task_dict: Task specification dictionary
            
        Returns:
            Created Task object
            
        Raises:
            ValueError: Invalid task structure
            TypeError: Invalid parameter types
            KeyError: Missing required 'type' field
            SecurityError: Dangerous task type or command detected
        """
        # Validate task dict structure
        if not isinstance(task_dict, dict):
            raise TypeError(f"Task must be dict, got {type(task_dict).__name__}")
        
        # Require 'type' field
        if "type" not in task_dict:
            raise KeyError("Task dictionary must have 'type' field")
        
        task_type = task_dict["type"]
        
        # Validate task type
        if not isinstance(task_type, str):
            raise TypeError(f"Task type must be string, got {type(task_type).__name__}")
        
        # Check for privilege escalation attempts
        if task_type in DANGEROUS_TASK_TYPES:
            raise SecurityError(
                f"Privilege escalation denied: task type '{task_type}' is not allowed"
            )
        
        # Validate task type against whitelist
        if task_type not in ALLOWED_TASK_TYPES:
            raise ValueError(
                f"Unknown task type: '{task_type}'. Allowed types: {sorted(ALLOWED_TASK_TYPES)}"
            )
        
        # Validate command field if present
        if "command" in task_dict:
            command = task_dict["command"]
            
            # Command must not be None or empty
            if command is None:
                raise ValueError("Task command cannot be None")
            
            if not isinstance(command, str):
                raise TypeError(f"Command must be string, got {type(command).__name__}")
            
            # Check for command injection attempts
            self._validate_command_safety(command)
        
        # Create description from type and command
        description = f"{task_type}"
        if "command" in task_dict:
            description += f": {task_dict['command'][:100]}"
        
        # Create task
        task = Task(
            description=description,
            parameters=task_dict,
            required_plugins=task_dict.get("required_plugins", []),
            priority=TaskPriority.NORMAL
        )
        
        self.tasks[task.id] = task
        self.task_queue.append(task)
        self.task_queue.sort(key=lambda t: t.priority.value, reverse=True)
        
        logger.info(f"Created task from dict: {description} ({task.id})")
        
        return task
    
    async def assign_task(self, task: Task, agent_id: Optional[str] = None) -> Optional[Agent]:
        """Assign task to an agent.
        
        Args:
            task: Task to assign
            agent_id: Specific agent ID to assign to (optional)
        
        Returns:
            Agent that was assigned the task, or None if no suitable agent
        
        Raises:
            ValueError: Invalid task or agent
        """
        # Validate task
        if not task:
            raise ValueError("Task cannot be None")
        
        # Sanitize task description
        if task.description:
            task.description = self._sanitize_task_description(task.description)
        
        # If specific agent requested, use it
        if agent_id:
            if agent_id not in self.agents:
                raise ValueError(f"Agent {agent_id} not found")
            
            agent = self.agents[agent_id]
            
            # Check if agent is available
            if agent.status != AgentStatus.IDLE:
                logger.warning(f"Agent {agent_id} is not idle: {agent.status}")
                return None
            
            # Assign task
            task.assigned_agent = agent_id
            task.status = TaskStatus.IN_PROGRESS
            logger.info(f"Assigned task {task.id} to agent {agent_id}")
            
            return agent
        
        # Otherwise, find suitable agent based on required capabilities
        for agent in self.agents.values():
            # Check if agent is available
            if agent.status != AgentStatus.IDLE:
                continue
            
            # Check if agent has required capabilities
            if task.required_capabilities:
                if not all(cap in agent.capabilities for cap in task.required_capabilities):
                    continue
            
            # Check if agent has required plugins
            if task.required_plugins:
                if not all(plugin in agent.plugins for plugin in task.required_plugins):
                    continue
            
            # Agent matches requirements
            task.assigned_agent = agent.id
            task.status = TaskStatus.IN_PROGRESS
            logger.info(f"Auto-assigned task {task.id} to agent {agent.id}")
            
            return agent
        
        # No suitable agent found
        logger.warning(f"No suitable agent found for task {task.id}")
        return None
    
    def _sanitize_task_description(self, description: str) -> str:
        """Sanitize task description to prevent XSS and injection attacks.
        
        Args:
            description: Task description to sanitize
            
        Returns:
            Sanitized description
        """
        if not description or not isinstance(description, str):
            return description
        
        # Characters that are dangerous and should be removed
        dangerous_chars = ['<', '>', '$', '{', '}', ';', '&', '|', '`']
        
        # Remove dangerous characters and patterns
        sanitized = description
        
        # Remove path traversal patterns
        while '../' in sanitized or '..\\' in sanitized:
            sanitized = sanitized.replace('../', '').replace('..\\', '')
        
        # Remove dangerous characters
        for char in dangerous_chars:
            sanitized = sanitized.replace(char, '')
        
        return sanitized

    def _validate_command_safety(self, command: str):
        """Validate command for security threats.
        
        Args:
            command: Command string to validate
            
        Raises:
            SecurityError: Command contains dangerous patterns
        """
        if not command or not isinstance(command, str):
            return
        
        # Normalize command for checking
        normalized = command.lower().strip()
        
        # Check for dangerous command patterns
        for dangerous in DANGEROUS_COMMANDS:
            if dangerous in normalized:
                raise SecurityError(
                    f"Command injection attempt detected: command contains '{dangerous}'"
                )
        
        # Check for shell operators that enable chaining
        shell_operators = ["&&", "||", "|", ";", "`", "$(", "${"]
        for operator in shell_operators:
            if operator in command:
                raise SecurityError(
                    f"Command injection attempt detected: command contains shell operator '{operator}'"
                )
        
        # Check for path traversal in commands
        if ".." in command or "~/" in command:
            raise SecurityError(
                "Path traversal attempt detected in command"
            )

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
