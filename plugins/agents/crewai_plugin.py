"""
CrewAI Plugin
Role-based multi-agent teams with hierarchical task delegation
"""

from typing import Dict, Any, Optional, List


class CrewAIPlugin:
    """Plugin for CrewAI role-based agent teams"""

    name = "crewai"
    version = "1.0.0"
    description = "Coordinate teams of AI agents with specific roles and goals"
    author = "Windows AI Team"

    def __init__(self):
        self.crews = {}
        self.agents = {}
        self.tasks = {}
        self._initialized = False

    def initialize(self, config: Optional[Dict[str, Any]] = None) -> bool:
        """Initialize the CrewAI plugin"""
        try:
            self._initialized = True
            return True
        except Exception as e:
            print(f"Error initializing CrewAI plugin: {e}")
            return False

    def execute(self, action: str, params: Dict[str, Any]) -> Dict[str, Any]:
        """Execute a CrewAI action"""
        if not self._initialized:
            return {"success": False, "error": "Plugin not initialized"}

        try:
            if action == "create_agent":
                return self._create_agent(params)
            elif action == "create_task":
                return self._create_task(params)
            elif action == "create_crew":
                return self._create_crew(params)
            elif action == "run_crew":
                return self._run_crew(params)
            elif action == "delegate_task":
                return self._delegate_task(params)
            elif action == "get_crew_status":
                return self._get_crew_status(params)
            else:
                return {"success": False, "error": f"Unknown action: {action}"}
        except Exception as e:
            return {"success": False, "error": str(e)}

    def _create_agent(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Create an agent with specific role and capabilities"""
        agent_id = params.get("id", f"agent_{len(self.agents)}")
        role = params.get("role", "")
        goal = params.get("goal", "")
        backstory = params.get("backstory", "")
        tools = params.get("tools", [])
        verbose = params.get("verbose", True)

        agent = {
            "id": agent_id,
            "role": role,
            "goal": goal,
            "backstory": backstory,
            "tools": tools,
            "verbose": verbose,
            "tasks_completed": 0,
            "status": "idle"
        }

        self.agents[agent_id] = agent

        return {
            "success": True,
            "agent": agent,
            "agent_id": agent_id
        }

    def _create_task(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Create a task to be assigned to an agent"""
        task_id = params.get("id", f"task_{len(self.tasks)}")
        description = params.get("description", "")
        expected_output = params.get("expected_output", "")
        agent_id = params.get("agent_id")
        context = params.get("context", [])  # Related tasks
        async_execution = params.get("async_execution", False)

        task = {
            "id": task_id,
            "description": description,
            "expected_output": expected_output,
            "agent_id": agent_id,
            "context": context,
            "async_execution": async_execution,
            "status": "pending",
            "result": None
        }

        self.tasks[task_id] = task

        return {
            "success": True,
            "task": task,
            "task_id": task_id
        }

    def _create_crew(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Create a crew of agents with assigned tasks"""
        crew_id = params.get("id", f"crew_{len(self.crews)}")
        agent_ids = params.get("agents", [])
        task_ids = params.get("tasks", [])
        process = params.get("process", "sequential")  # sequential or hierarchical
        verbose = params.get("verbose", True)
        manager_agent = params.get("manager_agent")  # For hierarchical process

        # Validate agents exist
        for agent_id in agent_ids:
            if agent_id not in self.agents:
                return {"success": False, "error": f"Agent {agent_id} not found"}

        # Validate tasks exist
        for task_id in task_ids:
            if task_id not in self.tasks:
                return {"success": False, "error": f"Task {task_id} not found"}

        crew = {
            "id": crew_id,
            "agents": agent_ids,
            "tasks": task_ids,
            "process": process,
            "verbose": verbose,
            "manager_agent": manager_agent,
            "status": "created",
            "results": []
        }

        self.crews[crew_id] = crew

        return {
            "success": True,
            "crew": crew,
            "crew_id": crew_id
        }

    def _run_crew(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Run a crew to execute all assigned tasks"""
        crew_id = params.get("crew_id", "")

        if crew_id not in self.crews:
            return {"success": False, "error": f"Crew {crew_id} not found"}

        crew = self.crews[crew_id]
        process = crew["process"]
        task_ids = crew["tasks"]
        agent_ids = crew["agents"]

        results = []

        if process == "sequential":
            # Execute tasks in order
            for task_id in task_ids:
                task = self.tasks[task_id]
                agent_id = task.get("agent_id") or agent_ids[0]

                if agent_id not in self.agents:
                    continue

                agent = self.agents[agent_id]

                # Simulate task execution
                task_result = self._execute_task(task, agent)
                results.append(task_result)

                # Update task and agent
                task["status"] = "completed"
                task["result"] = task_result["output"]
                agent["tasks_completed"] += 1

        elif process == "hierarchical":
            # Manager delegates tasks
            manager_id = crew.get("manager_agent") or agent_ids[0]
            manager = self.agents[manager_id]

            # Manager analyzes and delegates
            delegation_plan = {
                "manager": manager_id,
                "delegations": []
            }

            for task_id in task_ids:
                task = self.tasks[task_id]

                # Manager selects best agent for task
                assigned_agent = self._select_agent_for_task(task, agent_ids)
                task["agent_id"] = assigned_agent

                delegation_plan["delegations"].append({
                    "task_id": task_id,
                    "assigned_to": assigned_agent,
                    "reason": f"Best suited for {task['description'][:30]}..."
                })

                # Execute task
                agent = self.agents[assigned_agent]
                task_result = self._execute_task(task, agent)
                results.append(task_result)

                task["status"] = "completed"
                task["result"] = task_result["output"]
                agent["tasks_completed"] += 1

            results.insert(0, {
                "type": "delegation_plan",
                "plan": delegation_plan
            })

        crew["status"] = "completed"
        crew["results"] = results

        return {
            "success": True,
            "crew_id": crew_id,
            "process": process,
            "results": results,
            "tasks_completed": len([r for r in results if r.get("type") != "delegation_plan"])
        }

    def _execute_task(self, task: Dict[str, Any], agent: Dict[str, Any]) -> Dict[str, Any]:
        """Simulate task execution by an agent"""
        # Simulated execution
        output = f"[{agent['role']}] Completed: {task['description']}\n"
        output += f"Output: {task['expected_output']}"

        return {
            "task_id": task["id"],
            "agent_id": agent["id"],
            "agent_role": agent["role"],
            "output": output,
            "status": "success"
        }

    def _select_agent_for_task(self, task: Dict[str, Any], agent_ids: List[str]) -> str:
        """Manager selects best agent for a task based on role and capabilities"""
        # Simple selection: use task's assigned agent or first available
        if task.get("agent_id") and task["agent_id"] in agent_ids:
            return task["agent_id"]

        # Otherwise, select based on task keywords and agent roles
        task_desc = task["description"].lower()

        for agent_id in agent_ids:
            agent = self.agents[agent_id]
            role = agent["role"].lower()

            # Match keywords
            if "research" in task_desc and "research" in role:
                return agent_id
            elif "write" in task_desc and "writer" in role:
                return agent_id
            elif "analyze" in task_desc and "analyst" in role:
                return agent_id
            elif "code" in task_desc and ("engineer" in role or "developer" in role):
                return agent_id

        # Default: first agent
        return agent_ids[0]

    def _delegate_task(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Delegate a task from one agent to another"""
        from_agent_id = params.get("from_agent", "")
        to_agent_id = params.get("to_agent", "")
        task_id = params.get("task_id", "")
        reason = params.get("reason", "")

        if from_agent_id not in self.agents:
            return {"success": False, "error": f"From agent {from_agent_id} not found"}

        if to_agent_id not in self.agents:
            return {"success": False, "error": f"To agent {to_agent_id} not found"}

        if task_id not in self.tasks:
            return {"success": False, "error": f"Task {task_id} not found"}

        task = self.tasks[task_id]
        from_agent = self.agents[from_agent_id]
        to_agent = self.agents[to_agent_id]

        # Update task assignment
        old_agent = task.get("agent_id")
        task["agent_id"] = to_agent_id

        delegation = {
            "from": from_agent_id,
            "to": to_agent_id,
            "task_id": task_id,
            "reason": reason,
            "previous_agent": old_agent
        }

        return {
            "success": True,
            "delegation": delegation
        }

    def _get_crew_status(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Get status of a crew"""
        crew_id = params.get("crew_id", "")

        if crew_id not in self.crews:
            return {"success": False, "error": f"Crew {crew_id} not found"}

        crew = self.crews[crew_id]

        # Collect agent statuses
        agent_statuses = []
        for agent_id in crew["agents"]:
            if agent_id in self.agents:
                agent = self.agents[agent_id]
                agent_statuses.append({
                    "id": agent_id,
                    "role": agent["role"],
                    "tasks_completed": agent["tasks_completed"],
                    "status": agent["status"]
                })

        # Collect task statuses
        task_statuses = []
        for task_id in crew["tasks"]:
            if task_id in self.tasks:
                task = self.tasks[task_id]
                task_statuses.append({
                    "id": task_id,
                    "description": task["description"][:50] + "...",
                    "status": task["status"],
                    "assigned_to": task.get("agent_id")
                })

        return {
            "success": True,
            "crew_id": crew_id,
            "crew_status": crew["status"],
            "process": crew["process"],
            "agents": agent_statuses,
            "tasks": task_statuses,
            "results_count": len(crew.get("results", []))
        }

    def shutdown(self) -> bool:
        """Cleanup plugin resources"""
        self._initialized = False
        self.crews = {}
        self.agents = {}
        self.tasks = {}
        return True
