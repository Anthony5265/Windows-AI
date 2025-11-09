"""
BabyAGI Task Manager Plugin
Autonomous AI agent for task management and goal achievement
"""

import json
import asyncio
import logging
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime
import uuid


class Task:
    """Represents a task in the BabyAGI system"""

    def __init__(self, task_id: str, name: str, description: str = "", priority: int = 1):
        self.task_id = task_id
        self.name = name
        self.description = description
        self.priority = priority
        self.status = "pending"  # pending, in_progress, completed, failed
        self.created_at = datetime.now()
        self.completed_at = None
        self.result = None
        self.error = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "task_id": self.task_id,
            "name": self.name,
            "description": self.description,
            "priority": self.priority,
            "status": self.status,
            "created_at": self.created_at.isoformat(),
            "completed_at": self.completed_at.isoformat() if self.completed_at else None,
            "result": self.result,
            "error": self.error
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Task':
        task = cls(
            task_id=data["task_id"],
            name=data["name"],
            description=data.get("description", ""),
            priority=data.get("priority", 1)
        )
        task.status = data.get("status", "pending")
        task.result = data.get("result")
        task.error = data.get("error")
        if data.get("created_at"):
            task.created_at = datetime.fromisoformat(data["created_at"])
        if data.get("completed_at"):
            task.completed_at = datetime.fromisoformat(data["completed_at"])
        return task


class BabyAGIPlugin:
    """BabyAGI autonomous task management plugin"""

    def __init__(self):
        self.name = "babyagi"
        self.version = "1.0.0"
        self.description = "Autonomous AI agent for task management and goal achievement"
        self.logger = logging.getLogger(__name__)

        # Task management
        self.tasks: Dict[str, Task] = {}
        self.current_session_id: Optional[str] = None
        self.objective: Optional[str] = None
        self.max_iterations = 10
        self.current_iteration = 0

        # AI integration (will be injected)
        self.ai_client = None

        # Default settings
        self.default_settings = {
            "max_iterations": 10,
            "task_prioritization_prompt": "Given the objective: '{objective}', and the following tasks: {tasks}, prioritize them and return the most important task ID.",
            "task_creation_prompt": "Given the objective: '{objective}', and the result of task '{task_name}': {result}, create up to 3 new tasks to further the objective. Return as JSON array of task objects with 'name' and 'description' fields.",
            "task_execution_prompt": "Execute the following task: '{task_name}' - {task_description}. Objective: {objective}. Provide a detailed result."
        }

        self.settings = self.default_settings.copy()

    def initialize(self, config: Dict[str, Any]) -> bool:
        """Initialize the BabyAGI plugin"""
        try:
            self.settings.update(config.get("babyagi", {}))

            # Validate required AI client
            if not hasattr(self, 'ai_client') or self.ai_client is None:
                self.logger.warning("AI client not provided - BabyAGI will need external task execution")
                # This is okay - tasks can be executed manually or with external tools

            self.logger.info("BabyAGI plugin initialized successfully")
            return True

        except Exception as e:
            self.logger.error(f"Failed to initialize BabyAGI plugin: {e}")
            return False

    def execute(self, action: str, params: Dict[str, Any]) -> Dict[str, Any]:
        """Execute a BabyAGI action"""
        try:
            if action == "start_session":
                return self._start_session(params)
            elif action == "add_task":
                return self._add_task(params)
            elif action == "get_tasks":
                return self._get_tasks(params)
            elif action == "execute_task":
                return asyncio.run(self._execute_task_async(params))
            elif action == "complete_task":
                return self._complete_task(params)
            elif action == "prioritize_tasks":
                return asyncio.run(self._prioritize_tasks_async(params))
            elif action == "generate_new_tasks":
                return asyncio.run(self._generate_new_tasks_async(params))
            elif action == "run_autonomous_cycle":
                return asyncio.run(self._run_autonomous_cycle_async(params))
            elif action == "get_session_status":
                return self._get_session_status(params)
            else:
                return {"error": f"Unknown action: {action}"}

        except Exception as e:
            self.logger.error(f"Error executing action {action}: {e}")
            return {"error": str(e)}

    def _start_session(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Start a new BabyAGI session with an objective"""
        try:
            objective = params.get("objective", "")
            if not objective:
                return {"error": "Objective is required to start a session"}

            self.current_session_id = str(uuid.uuid4())
            self.objective = objective
            self.current_iteration = 0
            self.tasks = {}

            # Create initial task
            initial_task = Task(
                task_id=str(uuid.uuid4()),
                name="Analyze objective and create initial tasks",
                description=f"Break down the objective '{objective}' into actionable tasks",
                priority=1
            )
            self.tasks[initial_task.task_id] = initial_task

            return {
                "success": True,
                "session_id": self.current_session_id,
                "objective": self.objective,
                "initial_task": initial_task.to_dict(),
                "message": f"BabyAGI session started with objective: {objective}"
            }

        except Exception as e:
            self.logger.error(f"Error starting session: {e}")
            return {"error": f"Failed to start session: {str(e)}"}

    def _add_task(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Add a new task to the current session"""
        try:
            name = params.get("name", "")
            description = params.get("description", "")
            priority = params.get("priority", 1)

            if not name:
                return {"error": "Task name is required"}

            if not self.current_session_id:
                return {"error": "No active session. Start a session first."}

            task = Task(
                task_id=str(uuid.uuid4()),
                name=name,
                description=description,
                priority=priority
            )
            self.tasks[task.task_id] = task

            return {
                "success": True,
                "task": task.to_dict(),
                "message": f"Task '{name}' added successfully"
            }

        except Exception as e:
            self.logger.error(f"Error adding task: {e}")
            return {"error": f"Failed to add task: {str(e)}"}

    def _get_tasks(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Get tasks for the current session"""
        try:
            status_filter = params.get("status")  # Optional filter by status
            sort_by_priority = params.get("sort_by_priority", True)

            tasks = list(self.tasks.values())

            if status_filter:
                tasks = [t for t in tasks if t.status == status_filter]

            if sort_by_priority:
                tasks.sort(key=lambda t: (t.priority, t.created_at))

            return {
                "success": True,
                "tasks": [t.to_dict() for t in tasks],
                "session_id": self.current_session_id,
                "objective": self.objective,
                "total_tasks": len(tasks)
            }

        except Exception as e:
            self.logger.error(f"Error getting tasks: {e}")
            return {"error": f"Failed to get tasks: {str(e)}"}

    async def _execute_task_async(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Execute a specific task"""
        try:
            task_id = params.get("task_id", "")
            if not task_id or task_id not in self.tasks:
                return {"error": "Invalid task ID"}

            task = self.tasks[task_id]
            task.status = "in_progress"

            # If we have an AI client, use it to execute the task
            if self.ai_client:
                result = await self._execute_task_with_ai(task)
            else:
                # Manual execution - mark as completed with placeholder result
                result = f"Task '{task.name}' executed manually. Please provide result."
                task.status = "completed"
                task.completed_at = datetime.now()
                task.result = result

            return {
                "success": True,
                "task": task.to_dict(),
                "result": result,
                "message": f"Task '{task.name}' executed successfully"
            }

        except Exception as e:
            self.logger.error(f"Error executing task: {e}")
            if task_id in self.tasks:
                self.tasks[task_id].status = "failed"
                self.tasks[task_id].error = str(e)
            return {"error": f"Failed to execute task: {str(e)}"}

    async def _execute_task_with_ai(self, task: Task) -> str:
        """Execute a task using the AI client"""
        try:
            prompt = self.settings["task_execution_prompt"].format(
                task_name=task.name,
                task_description=task.description,
                objective=self.objective
            )

            # This assumes the AI client has a generate_text method
            # Adjust based on actual AI client interface
            if hasattr(self.ai_client, 'generate_text'):
                response = await self.ai_client.generate_text(prompt)
                result = response.get("text", "No result generated")
            elif hasattr(self.ai_client, 'chat'):
                messages = [{"role": "user", "content": prompt}]
                response = await self.ai_client.chat(messages)
                result = response.get("response", "No result generated")
            else:
                result = f"AI client does not support task execution. Task: {task.name}"

            task.status = "completed"
            task.completed_at = datetime.now()
            task.result = result

            return result

        except Exception as e:
            task.status = "failed"
            task.error = str(e)
            raise e

    def _complete_task(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Mark a task as completed with a result"""
        try:
            task_id = params.get("task_id", "")
            result = params.get("result", "")

            if not task_id or task_id not in self.tasks:
                return {"error": "Invalid task ID"}

            task = self.tasks[task_id]
            task.status = "completed"
            task.completed_at = datetime.now()
            task.result = result

            return {
                "success": True,
                "task": task.to_dict(),
                "message": f"Task '{task.name}' marked as completed"
            }

        except Exception as e:
            self.logger.error(f"Error completing task: {e}")
            return {"error": f"Failed to complete task: {str(e)}"}

    async def _prioritize_tasks_async(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Prioritize pending tasks using AI"""
        try:
            if not self.ai_client:
                return {"error": "AI client required for task prioritization"}

            pending_tasks = [t for t in self.tasks.values() if t.status == "pending"]
            if not pending_tasks:
                return {"success": True, "message": "No pending tasks to prioritize"}

            # Format tasks for AI
            task_list = "\n".join([f"- {t.name}: {t.description}" for t in pending_tasks])

            prompt = self.settings["task_prioritization_prompt"].format(
                objective=self.objective,
                tasks=task_list
            )

            # Get AI response
            if hasattr(self.ai_client, 'generate_text'):
                response = await self.ai_client.generate_text(prompt)
                prioritized_task_name = response.get("text", "").strip()
            elif hasattr(self.ai_client, 'chat'):
                messages = [{"role": "user", "content": prompt}]
                response = await self.ai_client.chat(messages)
                prioritized_task_name = response.get("response", "").strip()
            else:
                return {"error": "AI client does not support text generation"}

            # Find the prioritized task
            prioritized_task = None
            for task in pending_tasks:
                if task.name.lower() in prioritized_task_name.lower():
                    prioritized_task = task
                    break

            if not prioritized_task:
                prioritized_task = pending_tasks[0]  # Default to first task

            return {
                "success": True,
                "prioritized_task": prioritized_task.to_dict(),
                "message": f"Task '{prioritized_task.name}' prioritized"
            }

        except Exception as e:
            self.logger.error(f"Error prioritizing tasks: {e}")
            return {"error": f"Failed to prioritize tasks: {str(e)}"}

    async def _generate_new_tasks_async(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Generate new tasks based on completed task results"""
        try:
            completed_task_id = params.get("completed_task_id", "")
            if not completed_task_id or completed_task_id not in self.tasks:
                return {"error": "Invalid completed task ID"}

            completed_task = self.tasks[completed_task_id]
            if completed_task.status != "completed" or not completed_task.result:
                return {"error": "Task must be completed with a result to generate new tasks"}

            if not self.ai_client:
                return {"error": "AI client required for task generation"}

            prompt = self.settings["task_creation_prompt"].format(
                objective=self.objective,
                task_name=completed_task.name,
                result=completed_task.result
            )

            # Get AI response
            if hasattr(self.ai_client, 'generate_text'):
                response = await self.ai_client.generate_text(prompt)
                ai_response = response.get("text", "")
            elif hasattr(self.ai_client, 'chat'):
                messages = [{"role": "user", "content": prompt}]
                response = await self.ai_client.chat(messages)
                ai_response = response.get("response", "")
            else:
                return {"error": "AI client does not support text generation"}

            # Parse JSON response for new tasks
            try:
                new_tasks_data = json.loads(ai_response)
                if not isinstance(new_tasks_data, list):
                    new_tasks_data = [new_tasks_data]

                new_tasks = []
                for task_data in new_tasks_data[:3]:  # Limit to 3 new tasks
                    task = Task(
                        task_id=str(uuid.uuid4()),
                        name=task_data.get("name", "New Task"),
                        description=task_data.get("description", ""),
                        priority=2  # Lower priority than initial tasks
                    )
                    self.tasks[task.task_id] = task
                    new_tasks.append(task.to_dict())

                return {
                    "success": True,
                    "new_tasks": new_tasks,
                    "message": f"Generated {len(new_tasks)} new tasks"
                }

            except json.JSONDecodeError:
                return {"error": "AI response was not valid JSON for task creation"}

        except Exception as e:
            self.logger.error(f"Error generating new tasks: {e}")
            return {"error": f"Failed to generate new tasks: {str(e)}"}

    async def _run_autonomous_cycle_async(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Run one autonomous cycle of the BabyAGI loop"""
        try:
            if not self.current_session_id:
                return {"error": "No active session. Start a session first."}

            if self.current_iteration >= self.max_iterations:
                return {"error": "Maximum iterations reached"}

            self.current_iteration += 1

            # 1. Prioritize tasks
            prioritize_result = await self._prioritize_tasks_async({})
            if "error" in prioritize_result:
                return prioritize_result

            prioritized_task = self.tasks[prioritize_result["prioritized_task"]["task_id"]]

            # 2. Execute the prioritized task
            execute_result = await self._execute_task_async({"task_id": prioritized_task.task_id})
            if "error" in execute_result:
                return execute_result

            # 3. Generate new tasks based on the result
            generate_result = await self._generate_new_tasks_async({"completed_task_id": prioritized_task.task_id})
            if "error" in generate_result:
                # This is not a fatal error - we can continue without new tasks
                generate_result = {"new_tasks": []}

            # Check if objective is achieved
            objective_achieved = self._check_objective_achieved()

            return {
                "success": True,
                "iteration": self.current_iteration,
                "executed_task": execute_result["task"],
                "new_tasks": generate_result.get("new_tasks", []),
                "objective_achieved": objective_achieved,
                "message": f"Completed iteration {self.current_iteration}"
            }

        except Exception as e:
            self.logger.error(f"Error in autonomous cycle: {e}")
            return {"error": f"Failed to run autonomous cycle: {str(e)}"}

    def _check_objective_achieved(self) -> bool:
        """Check if the objective has been achieved"""
        # Simple heuristic: if we have no pending tasks, assume objective is achieved
        pending_tasks = [t for t in self.tasks.values() if t.status == "pending"]
        return len(pending_tasks) == 0

    def _get_session_status(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Get the current session status"""
        try:
            if not self.current_session_id:
                return {"error": "No active session"}

            total_tasks = len(self.tasks)
            completed_tasks = len([t for t in self.tasks.values() if t.status == "completed"])
            pending_tasks = len([t for t in self.tasks.values() if t.status == "pending"])
            failed_tasks = len([t for t in self.tasks.values() if t.status == "failed"])

            return {
                "success": True,
                "session_id": self.current_session_id,
                "objective": self.objective,
                "iteration": self.current_iteration,
                "max_iterations": self.max_iterations,
                "task_stats": {
                    "total": total_tasks,
                    "completed": completed_tasks,
                    "pending": pending_tasks,
                    "failed": failed_tasks
                },
                "objective_achieved": self._check_objective_achieved()
            }

        except Exception as e:
            self.logger.error(f"Error getting session status: {e}")
            return {"error": f"Failed to get session status: {str(e)}"}

    def update_settings(self, new_settings: Dict[str, Any]) -> bool:
        """Update plugin settings"""
        try:
            self.settings.update(new_settings)
            return True
        except Exception as e:
            self.logger.error(f"Failed to update settings: {e}")
            return False

    def get_settings(self) -> Dict[str, Any]:
        """Get current plugin settings"""
        return self.settings.copy()

    def cleanup(self):
        """Cleanup resources"""
        self.tasks.clear()
        self.current_session_id = None
        self.objective = None
        self.current_iteration = 0
        self.ai_client = None


# Plugin registration
plugin = BabyAGIPlugin()

def get_plugin():
    """Return plugin instance"""
    return plugin

def get_plugin_info():
    """Return plugin information"""
    return {
        "name": plugin.name,
        "version": plugin.version,
        "description": plugin.description,
        "type": "agent",
        "capabilities": ["task_management", "autonomous_execution", "goal_achievement"],
        "settings": plugin.default_settings
    }

# Plugin metadata for dynamic loading
PLUGIN_CLASS = BabyAGIPlugin
PLUGIN_NAME = "babyagi"
PLUGIN_VERSION = "1.0.0"
PLUGIN_DESCRIPTION = "Autonomous AI agent for task management and goal achievement"
PLUGIN_ACTIONS = [
    "start_session", "add_task", "get_tasks", "execute_task", "complete_task",
    "prioritize_tasks", "generate_new_tasks", "run_autonomous_cycle", "get_session_status"
]