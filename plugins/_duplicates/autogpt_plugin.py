"""
AutoGPT Agent Plugin
Autonomous AI agent that can break down tasks and execute them step by step
"""

from typing import Dict, Any, Optional, List
import os
import json
import logging
from datetime import datetime


class AutoGPTPlugin:
    """Plugin for AutoGPT autonomous agent"""

    name = "autogpt"
    version = "1.0.0"
    description = "Autonomous AI agent that breaks down tasks and executes them step by step"
    author = "Windows AI Team"

    def __init__(self):
        self.api_key: Optional[str] = None
        self.client = None
        self._initialized = False
        self.logger = logging.getLogger(__name__)
        self.max_iterations = 10
        self.current_task = None
        self.task_history = []

    def initialize(self, config: Optional[Dict[str, Any]] = None) -> bool:
        """Initialize the AutoGPT plugin"""
        try:
            # Try to import OpenAI client
            try:
                from openai import OpenAI
                self.client_class = OpenAI
            except ImportError:
                try:
                    import openai
                    self.client_class = openai.OpenAI
                except ImportError:
                    self.logger.error("OpenAI package not installed. Install with: pip install openai")
                    return False

            # Get API key from config or environment
            self.api_key = (
                config.get("api_key") if config
                else os.getenv("OPENAI_API_KEY")
            )

            if not self.api_key:
                self.logger.error("No OpenAI API key provided")
                return False

            self.client = self.client_class(api_key=self.api_key)

            # Get configuration settings
            self.max_iterations = config.get("max_iterations", 10) if config else 10
            self.model = config.get("model", "gpt-4") if config else "gpt-4"

            self._initialized = True
            self.logger.info("AutoGPT plugin initialized successfully")
            return True

        except Exception as e:
            self.logger.error(f"Error initializing AutoGPT plugin: {e}")
            return False

    def execute(self, action: str, params: Dict[str, Any]) -> Dict[str, Any]:
        """Execute an AutoGPT action"""
        if not self._initialized:
            return {"error": "Plugin not initialized. Please provide OpenAI API key."}

        try:
            if action == "run_task":
                return self._run_task(params)
            elif action == "plan_task":
                return self._plan_task(params)
            elif action == "execute_step":
                return self._execute_step(params)
            elif action == "reflect_and_adjust":
                return self._reflect_and_adjust(params)
            else:
                return {"error": f"Unknown action: {action}"}

        except Exception as e:
            self.logger.error(f"Error executing action {action}: {e}")
            return {"error": str(e)}

    def _run_task(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Run a complete autonomous task"""
        goal = params.get("goal", "")
        if not goal:
            return {"error": "No goal provided"}

        self.current_task = {
            "goal": goal,
            "start_time": datetime.now().isoformat(),
            "steps": [],
            "status": "running"
        }

        try:
            # Plan the task
            plan_result = self._plan_task({"goal": goal})
            if not plan_result.get("success", False):
                return plan_result

            steps = plan_result.get("steps", [])

            # Execute each step
            results = []
            for i, step in enumerate(steps):
                step_params = {
                    "step": step,
                    "step_number": i + 1,
                    "total_steps": len(steps),
                    "goal": goal,
                    "previous_results": results
                }

                step_result = self._execute_step(step_params)
                results.append(step_result)

                # Check if step failed critically
                if not step_result.get("success", False):
                    break

                # Limit iterations
                if i >= self.max_iterations:
                    break

            # Final reflection
            reflection = self._reflect_and_adjust({
                "goal": goal,
                "steps": steps,
                "results": results
            })

            self.current_task["status"] = "completed"
            self.current_task["end_time"] = datetime.now().isoformat()
            self.task_history.append(self.current_task)

            return {
                "success": True,
                "goal": goal,
                "steps_executed": len(results),
                "results": results,
                "reflection": reflection,
                "task_id": len(self.task_history)
            }

        except Exception as e:
            self.current_task["status"] = "failed"
            self.current_task["error"] = str(e)
            return {"error": f"Task execution failed: {e}"}

    def _plan_task(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Plan a task by breaking it down into steps"""
        goal = params.get("goal", "")

        system_prompt = """You are an autonomous AI agent. Your task is to break down complex goals into actionable steps.

For the given goal, create a step-by-step plan. Each step should be:
1. Specific and actionable
2. Independent where possible
3. Verifiable (you should be able to check if it was completed)

Return your response as a JSON object with a "steps" array containing the step descriptions."""

        user_prompt = f"Goal: {goal}\n\nCreate a detailed step-by-step plan to accomplish this goal."

        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                temperature=0.3,
                max_tokens=1000
            )

            content = response.choices[0].message.content.strip()

            # Try to parse JSON response
            try:
                plan_data = json.loads(content)
                steps = plan_data.get("steps", [])
            except json.JSONDecodeError:
                # Fallback: extract steps from text
                lines = content.split('\n')
                steps = [line.strip('- ').strip() for line in lines if line.strip() and not line.startswith('```')]

            return {
                "success": True,
                "steps": steps,
                "goal": goal
            }

        except Exception as e:
            self.logger.error(f"Error planning task: {e}")
            return {"error": f"Failed to plan task: {e}"}

    def _execute_step(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Execute a single step of the task"""
        step = params.get("step", "")
        step_number = params.get("step_number", 1)
        total_steps = params.get("total_steps", 1)
        goal = params.get("goal", "")
        previous_results = params.get("previous_results", [])

        system_prompt = f"""You are executing step {step_number} of {total_steps} for the goal: {goal}

Previous results: {json.dumps(previous_results, indent=2)}

Execute this step: {step}

Provide a detailed execution plan and result. Be thorough and check your work."""

        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": f"Execute this step: {step}"}
                ],
                temperature=0.2,
                max_tokens=1500
            )

            result = response.choices[0].message.content.strip()

            # Store step result
            step_result = {
                "step_number": step_number,
                "step": step,
                "result": result,
                "success": True,
                "timestamp": datetime.now().isoformat()
            }

            if self.current_task:
                self.current_task["steps"].append(step_result)

            return step_result

        except Exception as e:
            self.logger.error(f"Error executing step {step_number}: {e}")
            return {
                "step_number": step_number,
                "step": step,
                "success": False,
                "error": str(e),
                "timestamp": datetime.now().isoformat()
            }

    def _reflect_and_adjust(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Reflect on task execution and provide final assessment"""
        goal = params.get("goal", "")
        steps = params.get("steps", [])
        results = params.get("results", [])

        system_prompt = """You are an autonomous AI agent reflecting on task completion.

Analyze the goal, steps taken, and results achieved. Provide:
1. Assessment of goal completion
2. What worked well
3. What could be improved
4. Final recommendations"""

        reflection_prompt = f"""
Goal: {goal}
Steps planned: {len(steps)}
Steps executed: {len(results)}

Results summary:
{json.dumps(results, indent=2)}

Provide your final reflection and assessment."""

        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": reflection_prompt}
                ],
                temperature=0.3,
                max_tokens=1000
            )

            reflection = response.choices[0].message.content.strip()

            return {
                "success": True,
                "reflection": reflection,
                "goal_completion_assessment": "completed" if len(results) == len(steps) else "partial",
                "steps_completed": len(results),
                "steps_planned": len(steps)
            }

        except Exception as e:
            self.logger.error(f"Error in reflection: {e}")
            return {"error": f"Failed to reflect on task: {e}"}

    def get_task_history(self) -> List[Dict[str, Any]]:
        """Get history of executed tasks"""
        return self.task_history.copy()

    def get_current_task_status(self) -> Optional[Dict[str, Any]]:
        """Get status of currently running task"""
        return self.current_task.copy() if self.current_task else None

    def cleanup(self):
        """Cleanup resources"""
        self.client = None
        self._initialized = False
        self.current_task = None
        self.task_history = []


# Plugin metadata
PLUGIN_CLASS = AutoGPTPlugin
PLUGIN_NAME = "autogpt"
PLUGIN_VERSION = "1.0.0"
PLUGIN_DESCRIPTION = "Autonomous AI agent that breaks down tasks and executes them step by step"
PLUGIN_ACTIONS = ["run_task", "plan_task", "execute_step", "reflect_and_adjust"]