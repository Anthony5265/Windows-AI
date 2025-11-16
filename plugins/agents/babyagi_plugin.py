"""
BabyAGI Plugin
Task-driven autonomous agent with dynamic task generation
"""

from typing import Dict, Any, Optional, List
from collections import deque


class BabyAGIPlugin:
    """Plugin for BabyAGI autonomous agent"""

    name = "babyagi"
    version = "1.0.0"
    description = "Task-driven autonomous agent with task prioritization"
    author = "Windows AI Team"

    def __init__(self):
        self.task_list = deque()
        self.completed_tasks = []
        self.objective = ""
        self._initialized = False

    def initialize(self, config: Optional[Dict[str, Any]] = None) -> bool:
        """Initialize the BabyAGI plugin"""
        try:
            self._initialized = True
            return True
        except Exception as e:
            print(f"Error initializing BabyAGI plugin: {e}")
            return False

    def execute(self, action: str, params: Dict[str, Any]) -> Dict[str, Any]:
        """Execute a BabyAGI action"""
        if not self._initialized:
            return {"success": False, "error": "Plugin not initialized"}

        try:
            if action == "set_objective":
                return self._set_objective(params)
            elif action == "add_task":
                return self._add_task(params)
            elif action == "execute_task":
                return self._execute_task()
            elif action == "prioritize_tasks":
                return self._prioritize_tasks()
            elif action == "create_new_tasks":
                return self._create_new_tasks(params)
            elif action == "get_status":
                return self._get_status()
            else:
                return {"success": False, "error": f"Unknown action: {action}"}
        except Exception as e:
            return {"success": False, "error": str(e)}

    def _set_objective(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Set the main objective"""
        self.objective = params.get("objective", "")

        # Create initial task
        initial_task = {
            "id": 1,
            "task": f"Develop a plan to: {self.objective}",
            "priority": 1
        }
        self.task_list.append(initial_task)

        return {
            "success": True,
            "objective": self.objective,
            "initial_tasks": list(self.task_list)
        }

    def _add_task(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Add a task to the list"""
        task_description = params.get("task", "")
        priority = params.get("priority", 5)

        task = {
            "id": len(self.task_list) + len(self.completed_tasks) + 1,
            "task": task_description,
            "priority": priority
        }

        self.task_list.append(task)

        return {
            "success": True,
            "task": task,
            "queue_length": len(self.task_list)
        }

    def _execute_task(self) -> Dict[str, Any]:
        """Execute the next task"""
        if not self.task_list:
            return {
                "success": False,
                "error": "No tasks in queue"
            }

        current_task = self.task_list.popleft()

        # Simulated task execution
        result = f"Completed: {current_task['task']}"

        self.completed_tasks.append({
            **current_task,
            "result": result,
            "status": "completed"
        })

        return {
            "success": True,
            "task": current_task,
            "result": result,
            "remaining_tasks": len(self.task_list)
        }

    def _prioritize_tasks(self) -> Dict[str, Any]:
        """Re-prioritize task queue"""
        # Sort tasks by priority
        sorted_tasks = sorted(self.task_list, key=lambda x: x.get("priority", 5))
        self.task_list = deque(sorted_tasks)

        return {
            "success": True,
            "task_order": list(self.task_list),
            "count": len(self.task_list)
        }

    def _create_new_tasks(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Create new tasks based on previous result"""
        previous_result = params.get("result", "")
        incomplete_tasks = list(self.task_list)

        # Simulated new task creation
        new_tasks = [
            {"id": len(self.task_list) + len(self.completed_tasks) + i + 1,
             "task": f"Follow-up task {i+1} based on: {previous_result[:30]}...",
             "priority": 5}
            for i in range(2)
        ]

        for task in new_tasks:
            self.task_list.append(task)

        return {
            "success": True,
            "new_tasks": new_tasks,
            "total_tasks": len(self.task_list)
        }

    def _get_status(self) -> Dict[str, Any]:
        """Get current agent status"""
        return {
            "success": True,
            "objective": self.objective,
            "pending_tasks": len(self.task_list),
            "completed_tasks": len(self.completed_tasks),
            "task_queue": list(self.task_list)[:5],  # First 5 tasks
            "recent_completions": self.completed_tasks[-5:]  # Last 5 completed
        }

    def shutdown(self) -> bool:
        """Cleanup plugin resources"""
        self._initialized = False
        self.task_list = deque()
        self.completed_tasks = []
        return True
