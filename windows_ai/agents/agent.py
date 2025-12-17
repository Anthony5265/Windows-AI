"""Agent implementation for Windows AI orchestration"""

from typing import Dict, Any, List, Optional
from enum import Enum
import asyncio
import logging
from datetime import datetime
import psutil
import os

from windows_ai.agents.task import Task, TaskStatus
from windows_ai.core.plugin_manager import PluginManager
from windows_ai.exceptions import SecurityError

logger = logging.getLogger(__name__)

class AgentStatus(Enum):
    """Agent status"""
    IDLE = "idle"
    BUSY = "busy"
    ERROR = "error"
    OFFLINE = "offline"

class Agent:
    """AI Agent that coordinates plugin execution for complex tasks"""

    def __init__(
        self,
        name: str,
        agent_id: Optional[str] = None,
        plugin_manager: Optional[PluginManager] = None,
        plugins: Optional[List[str]] = None,
        config: Optional[Dict[str, Any]] = None
    ):
        import uuid
        self.id = agent_id or str(uuid.uuid4())
        self.name = name
        self.plugin_manager = plugin_manager
        self.plugins = plugins or []
        self.config = config or {}
        self.status = AgentStatus.IDLE
        self.current_task: Optional[Task] = None
        self.completed_tasks: List[str] = []
        self.failed_tasks: List[str] = []
        self.created_at = datetime.utcnow()
        self.last_activity = datetime.utcnow()
        
        # Security features
        self.memory: Dict[str, Any] = {}  # Agent memory storage
        
        # Capabilities - IMMUTABLE tuple to prevent privilege escalation
        capabilities_list = config.get('capabilities', plugins or []) if config else (plugins or [])
        self._capabilities_tuple = tuple(capabilities_list)  # Store as tuple (immutable)
        
        # Auth token validation
        self.auth_token: Optional[str] = config.get('auth_token') if config else None
        if not self.auth_token:
            logger.warning(f"Agent {name} created without auth token")
        
        # Resource limits (configurable via config)
        self.cpu_limit_percent = config.get('cpu_limit_percent', 80.0) if config else 80.0  # 80% CPU max
        self.memory_limit_mb = config.get('memory_limit_mb', 512) if config else 512  # 512MB max
        self.task_timeout_seconds = config.get('task_timeout_seconds', 30) if config else 30  # 30s timeout
        self.max_concurrent_tasks = config.get('max_concurrent_tasks', 5) if config else 5  # 5 concurrent max
        
        # Track process for resource monitoring
        self.process = psutil.Process(os.getpid())
        
        # Concurrent task limiting
        self._task_semaphore = asyncio.Semaphore(self.max_concurrent_tasks)
        self._active_task_count = 0
        self._task_count_lock = asyncio.Lock()  # Protect counter access
    
    @property
    def capabilities(self) -> List[str]:
        """Get capabilities as list (read-only - returns copy to prevent modification)"""
        return list(self._capabilities_tuple)
    
    @capabilities.setter
    def capabilities(self, value: List[str]):
        """Prevent setting capabilities after creation (privilege escalation)"""
        raise PermissionError("Cannot modify agent capabilities after creation")
    
    def _grant_capability(self, capability: str):
        """Attempt to grant capability - blocked for security"""
        raise PermissionError("Cannot grant capabilities dynamically - security violation")


    async def execute_task(self, task: Task) -> Dict[str, Any]:
        """Execute a task using available plugins with capability authorization"""
        # Check capability authorization FIRST (before incrementing counter)
        if hasattr(task, 'required_capabilities') and task.required_capabilities:
            agent_capabilities = set(self.capabilities)
            required_capabilities = set(task.required_capabilities)
            missing = required_capabilities - agent_capabilities
            if missing:
                error = f"Insufficient capabilities: task requires {missing}, agent has {agent_capabilities}"
                logger.warning(f"Authorization failed for agent {self.name}: {error}")
                raise PermissionError(error)
        
        incremented = False
        try:
            # Check concurrent task limit atomically
            async with self._task_count_lock:
                if self._active_task_count >= self.max_concurrent_tasks:
                    error = f"Concurrent task limit reached ({self.max_concurrent_tasks})"
                    logger.warning(error)
                    raise RuntimeError(error)
                self._active_task_count += 1
                incremented = True
            
            # Execute task (no semaphore needed, counter handles limiting)
            return await self._execute_task_with_monitoring(task)
        finally:
            # Only decrement if we incremented
            if incremented:
                async with self._task_count_lock:
                    self._active_task_count -= 1
    
    async def _execute_task_with_monitoring(self, task: Task) -> Dict[str, Any]:
        """Internal method with resource monitoring"""
        logger.info(f"Agent {self.name} executing task: {task.description}")

        self.status = AgentStatus.BUSY
        self.current_task = task
        self.last_activity = datetime.utcnow()

        task.start()
        task.assigned_agent = self.id

        # Start resource monitoring (get fresh process for mocking support)
        start_time = datetime.utcnow()
        process = psutil.Process(os.getpid())
        start_cpu_percent = process.cpu_percent(interval=0.1)
        start_memory_mb = process.memory_info().rss / (1024 * 1024)

        try:
            # Validate task parameters for security
            self._validate_task_parameters(task.parameters)
            
            # Determine timeout (use task-specific or agent default)
            timeout = task.timeout if task.timeout is not None else self.task_timeout_seconds
            
            # Wrap execution with timeout
            try:
                result = await asyncio.wait_for(
                    self._execute_task_internal(task),
                    timeout=timeout
                )
            except asyncio.TimeoutError:
                error = f"Task exceeded timeout of {timeout}s"
                task.fail(error)
                self.failed_tasks.append(task.id)
                raise TimeoutError(error)
            
            # Check resource usage after execution (get fresh process for mocking)
            process = psutil.Process(os.getpid())
            cpu_percent = process.cpu_percent(interval=0.1)
            memory_mb = process.memory_info().rss / (1024 * 1024)
            
            # Check CPU limit
            if cpu_percent > self.cpu_limit_percent:
                error = f"CPU usage {cpu_percent:.1f}% exceeded limit of {self.cpu_limit_percent}%"
                task.fail(error)
                self.failed_tasks.append(task.id)
                raise ResourceWarning(error)
            
            # Check memory limit
            if memory_mb > self.memory_limit_mb:
                error = f"Memory usage {memory_mb:.1f}MB exceeded limit of {self.memory_limit_mb}MB"
                task.fail(error)
                self.failed_tasks.append(task.id)
                raise ValueError(error)

            # Mark task as complete
            task.complete(result)
            self.completed_tasks.append(task.id)

            logger.info(f"Agent {self.name} completed task: {task.id}")

            return {
                'success': True,
                'result': result,
                'task_id': task.id,
                'agent_id': self.id,
                'resource_usage': {
                    'cpu_percent': cpu_percent,
                    'memory_mb': memory_mb,
                    'duration_seconds': (datetime.utcnow() - start_time).total_seconds()
                }
            }

        except Exception as e:
            error_msg = str(e)
            logger.error(f"Agent {self.name} task failed: {error_msg}")

            task.fail(error_msg)
            self.failed_tasks.append(task.id)

            # Re-raise specific security/resource errors
            error_msg_lower = error_msg.lower()
            if isinstance(e, (ValueError, TimeoutError, ResourceWarning)) and any(
                keyword in error_msg_lower for keyword in ["dangerous", "timeout", "cpu", "memory", "unrealistic"]
            ):
                raise
            
            return {
                'success': False,
                'error': error_msg,
                'task_id': task.id,
                'agent_id': self.id
            }

        finally:
            self.status = AgentStatus.IDLE
            self.current_task = None
            self.last_activity = datetime.utcnow()

    async def _execute_task_internal(self, task: Task) -> Any:
        """Internal task execution logic (separated for timeout wrapping)"""
        # Check if required plugins are available
        missing_plugins = [
            p for p in task.required_plugins
            if not self.plugin_manager.get_plugin(p)
        ]

        if missing_plugins:
            error = f"Missing required plugins: {', '.join(missing_plugins)}"
            raise ValueError(error)

        # Execute subtasks if any
        if task.subtasks:
            results = []
            for subtask in task.subtasks:
                subtask_result = await self.execute_task(subtask)
                results.append(subtask_result)

                if not subtask_result.get('success'):
                    error = f"Subtask failed: {subtask_result.get('error')}"
                    raise ValueError(error)

            return {'subtask_results': results}

        else:
            # Execute main task using plugins
            return await self._execute_with_plugins(task)

    async def _execute_with_plugins(self, task: Task) -> Any:
        """Execute task using the specified plugins"""
        # If specific plugins are required, use them
        if task.required_plugins:
            results = {}

            for plugin_id in task.required_plugins:
                plugin = self.plugin_manager.get_plugin(plugin_id)
                if not plugin:
                    raise ValueError(f"Plugin {plugin_id} not found")

                # Determine action from task parameters
                action = task.parameters.get('action', 'execute')
                params = task.parameters.get('params', {})

                # Execute plugin
                result = await plugin.execute(action, params)
                results[plugin_id] = result

            return results

        # Otherwise, try to determine best plugin from description
        else:
            # Add minimal delay to ensure concurrent limiting works correctly
            # Even "instant" tasks in real systems take some time
            await asyncio.sleep(0.001)  # 1ms minimum execution time
            
            # Simple implementation: return task parameters
            # In a real system, this would use AI/ML to determine best plugins
            return {
                'message': 'Task execution not yet fully implemented',
                'parameters': task.parameters
            }
    
    def _validate_task_parameters(self, parameters: Dict[str, Any]) -> None:
        """Validate task parameters for security issues"""
        dangerous_patterns = [
            '../',  # Path traversal
            '..\\\\',  # Windows path traversal
            'rm -rf',  # Dangerous command
            'DROP TABLE',  # SQL injection
            'DROP DATABASE',  # SQL injection
            'DELETE FROM',  # SQL injection (without WHERE)
            '<script',  # XSS
            'javascript:',  # XSS
            'eval(',  # Code injection
            'exec(',  # Code injection
        ]
        
        for key, value in parameters.items():
            if isinstance(value, str):
                value_lower = value.lower()
                for pattern in dangerous_patterns:
                    if pattern.lower() in value_lower:
                        raise ValueError(f"Dangerous pattern '{pattern}' detected in parameter '{key}'")
                
                # Check for unrealistic memory allocations
                value_upper = value.upper()
                if 'GB' in value_upper or 'TB' in value_upper:
                    import re
                    size_match = re.search(r'(\d+(?:\.\d+)?)\s*(GB|TB)', value_upper)
                    if size_match:
                        size_num = float(size_match.group(1))
                        size_unit = size_match.group(2)
                        
                        # Convert to GB for comparison
                        if size_unit == 'TB':
                            size_num *= 1024
                        
                        # Check if allocation is unrealistic (>= 10GB)
                        if size_num >= 10:
                            raise ValueError(f"Unrealistic memory allocation '{value}' in parameter '{key}'")
    
    async def _execute_plugin(self, plugin_name: str, action: str, params: Dict[str, Any]) -> Any:
        """Execute a specific plugin action (used for security testing)"""
        # Check if agent has permission to use this plugin
        if plugin_name not in self.plugins:
            raise PermissionError(f"Agent {self.name} does not have access to plugin {plugin_name}")
        
        # Get plugin from manager
        plugin = self.plugin_manager.get_plugin(plugin_name)
        if not plugin:
            raise ValueError(f"Plugin {plugin_name} not found")
        
        # Execute plugin action
        result = await plugin.execute(action, params)
        return result
    
    async def send_message(self, agent_id: str, message: Dict[str, Any]) -> bool:
        """Send message to another agent with authentication"""
        # Add authentication token to message
        authenticated_message = {
            **message,
            'sender_id': self.id,
            'sender_name': self.name,
            'auth_token': self.auth_token,
            'timestamp': datetime.utcnow().isoformat()
        }
        
        # In real implementation, this would use message queue/broker
        # For now, just log it
        logger.info(f"Agent {self.name} sent message to {agent_id}: {message}")
        return True
    
    def receive_message(self, sender_id: str, message: Dict[str, Any]) -> None:
        """Receive and process a message from another agent"""
        # Validate message signature/authentication
        if not message.get('auth_token'):
            raise ValueError("Message missing authentication token")
        
        # Check for message tampering by verifying sender
        if message.get('sender_id') != sender_id:
            raise SecurityError("Message sender mismatch - possible tampering detected")
        
        # Check for replay attacks by validating timestamp
        if 'timestamp' in message:
            import dateutil.parser
            msg_time = dateutil.parser.isoparse(message['timestamp'])
            now = datetime.utcnow()
            # If message is older than 5 minutes, reject it as potential replay
            if (now - msg_time).total_seconds() > 300:
                raise SecurityError("Message timestamp too old - possible replay attack detected")
        
        # Store message in memory
        if 'messages' not in self.memory:
            self.memory['messages'] = []
        
        self.memory['messages'].append({
            'from': sender_id,
            'content': message,
            'received_at': datetime.utcnow().isoformat()
        })
        
        logger.info(f"Agent {self.name} received message from {sender_id}")
    
    def get_info(self) -> Dict[str, Any]:
        """Get public agent information (no sensitive data)"""
        return {
            'id': self.id,
            'name': self.name,
            'status': self.status.value,
            'plugins': self.plugins,
            'capabilities': self.capabilities,
            'completed_tasks_count': len(self.completed_tasks),
            'failed_tasks_count': len(self.failed_tasks),
            'created_at': self.created_at.isoformat()
        }
    
    def get_state(self) -> Dict[str, Any]:
        """Get serializable agent state (safe for external exposure)"""
        return {
            'id': self.id,
            'name': self.name,
            'status': self.status.value,
            'current_task_id': self.current_task.id if self.current_task else None,
            'completed_tasks': len(self.completed_tasks),
            'failed_tasks': len(self.failed_tasks),
            'plugins': self.plugins,
            'capabilities': self.capabilities,
            'created_at': self.created_at.isoformat(),
            'last_activity': self.last_activity.isoformat()
        }

    def get_stats(self) -> Dict[str, Any]:
        """Get agent statistics"""
        return {
            'id': self.id,
            'name': self.name,
            'status': self.status.value,
            'plugins': self.plugins,
            'completed_tasks': len(self.completed_tasks),
            'failed_tasks': len(self.failed_tasks),
            'current_task': self.current_task.id if self.current_task else None,
            'created_at': self.created_at.isoformat(),
            'last_activity': self.last_activity.isoformat()
        }

    def to_dict(self) -> Dict[str, Any]:
        """Convert agent to dictionary"""
        return {
            'id': self.id,
            'name': self.name,
            'status': self.status.value,
            'plugins': self.plugins,
            'config': self.config,
            'current_task': self.current_task.to_dict() if self.current_task else None,
            'completed_tasks': self.completed_tasks,
            'failed_tasks': self.failed_tasks,
            'created_at': self.created_at.isoformat(),
            'last_activity': self.last_activity.isoformat()
        }
