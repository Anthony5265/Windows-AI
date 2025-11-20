"""Agent implementation for Windows AI orchestration"""

from typing import Dict, Any, List, Optional
from enum import Enum
import asyncio
import logging
from datetime import datetime

from windows_ai.agents.task import Task, TaskStatus
from windows_ai.core.plugin_manager import PluginManager

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
        agent_id: str,
        name: str,
        plugin_manager: PluginManager,
        plugins: Optional[List[str]] = None,
        config: Optional[Dict[str, Any]] = None
    ):
        self.id = agent_id
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

    async def execute_task(self, task: Task) -> Dict[str, Any]:
        """Execute a task using available plugins"""
        logger.info(f"Agent {self.name} executing task: {task.description}")

        self.status = AgentStatus.BUSY
        self.current_task = task
        self.last_activity = datetime.utcnow()

        task.start()
        task.assigned_agent = self.id

        try:
            # Check if required plugins are available
            missing_plugins = [
                p for p in task.required_plugins
                if not self.plugin_manager.get_plugin(p)
            ]

            if missing_plugins:
                error = f"Missing required plugins: {', '.join(missing_plugins)}"
                task.fail(error)
                self.failed_tasks.append(task.id)
                return {'success': False, 'error': error}

            # Execute subtasks if any
            if task.subtasks:
                results = []
                for subtask in task.subtasks:
                    subtask_result = await self.execute_task(subtask)
                    results.append(subtask_result)

                    if not subtask_result.get('success'):
                        error = f"Subtask failed: {subtask_result.get('error')}"
                        task.fail(error)
                        self.failed_tasks.append(task.id)
                        return {'success': False, 'error': error}

                result = {'subtask_results': results}

            else:
                # Execute main task using plugins
                result = await self._execute_with_plugins(task)

            # Mark task as complete
            task.complete(result)
            self.completed_tasks.append(task.id)

            logger.info(f"Agent {self.name} completed task: {task.id}")

            return {
                'success': True,
                'result': result,
                'task_id': task.id,
                'agent_id': self.id
            }

        except Exception as e:
            error_msg = str(e)
            logger.error(f"Agent {self.name} task failed: {error_msg}")

            task.fail(error_msg)
            self.failed_tasks.append(task.id)

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
            # Simple implementation: return task parameters
            # In a real system, this would use AI/ML to determine best plugins
            return {
                'message': 'Task execution not yet fully implemented',
                'parameters': task.parameters
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
