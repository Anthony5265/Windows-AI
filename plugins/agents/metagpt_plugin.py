"""
MetaGPT Plugin
Multi-agent collaboration with software company simulation
"""

from typing import Dict, Any, Optional, List
from collections import deque


class MetaGPTPlugin:
    """Plugin for MetaGPT multi-agent collaboration"""

    name = "metagpt"
    version = "1.0.0"
    description = "Multi-agent collaboration framework simulating software company roles"
    author = "Windows AI Team"

    def __init__(self):
        self.agents = {}
        self.project = None
        self.task_queue = deque()
        self.history = []
        self._initialized = False

    def initialize(self, config: Optional[Dict[str, Any]] = None) -> bool:
        """Initialize the MetaGPT plugin"""
        try:
            # Initialize default agent roles
            self.agents = {
                "product_manager": {
                    "role": "Product Manager",
                    "responsibilities": ["requirements", "prd", "user_stories"],
                    "active": True
                },
                "architect": {
                    "role": "Architect",
                    "responsibilities": ["system_design", "architecture", "tech_stack"],
                    "active": True
                },
                "project_manager": {
                    "role": "Project Manager",
                    "responsibilities": ["planning", "task_breakdown", "scheduling"],
                    "active": True
                },
                "engineer": {
                    "role": "Engineer",
                    "responsibilities": ["implementation", "coding", "testing"],
                    "active": True
                },
                "qa": {
                    "role": "QA Engineer",
                    "responsibilities": ["testing", "quality_assurance", "bug_reporting"],
                    "active": True
                }
            }
            self._initialized = True
            return True
        except Exception as e:
            print(f"Error initializing MetaGPT plugin: {e}")
            return False

    def execute(self, action: str, params: Dict[str, Any]) -> Dict[str, Any]:
        """Execute a MetaGPT action"""
        if not self._initialized:
            return {"success": False, "error": "Plugin not initialized"}

        try:
            if action == "create_project":
                return self._create_project(params)
            elif action == "run_workflow":
                return self._run_workflow(params)
            elif action == "agent_communicate":
                return self._agent_communicate(params)
            elif action == "get_deliverable":
                return self._get_deliverable(params)
            elif action == "add_agent":
                return self._add_agent(params)
            elif action == "get_project_status":
                return self._get_project_status()
            else:
                return {"success": False, "error": f"Unknown action: {action}"}
        except Exception as e:
            return {"success": False, "error": str(e)}

    def _create_project(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Create a new software project"""
        project_idea = params.get("idea", "")

        self.project = {
            "idea": project_idea,
            "status": "initiated",
            "deliverables": {},
            "current_phase": "requirements"
        }

        # Product Manager creates PRD
        prd = {
            "title": f"Product Requirements Document: {project_idea}",
            "goals": [
                f"Implement {project_idea}",
                "Ensure high code quality",
                "Deliver within timeline"
            ],
            "user_stories": [
                f"As a user, I want to use {project_idea}",
                "As a developer, I want maintainable code"
            ],
            "requirements": [
                "Functional requirements",
                "Non-functional requirements"
            ]
        }

        self.project["deliverables"]["prd"] = prd

        return {
            "success": True,
            "project": self.project,
            "initial_deliverable": "prd",
            "next_agent": "architect"
        }

    def _run_workflow(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Run the multi-agent workflow"""
        if not self.project:
            return {"success": False, "error": "No project created"}

        workflow_steps = []

        # Phase 1: Product Manager - PRD
        pm_output = {
            "agent": "product_manager",
            "phase": "requirements",
            "output": self.project["deliverables"].get("prd", {}),
            "next_agent": "architect"
        }
        workflow_steps.append(pm_output)
        self.history.append(pm_output)

        # Phase 2: Architect - System Design
        design_doc = {
            "architecture": "Modular architecture with plugin system",
            "components": ["Core Engine", "Plugin Manager", "API Layer"],
            "tech_stack": ["Python", "FastAPI", "PostgreSQL"],
            "data_flow": "Request -> API -> Core -> Plugins -> Response"
        }
        self.project["deliverables"]["design"] = design_doc

        arch_output = {
            "agent": "architect",
            "phase": "design",
            "output": design_doc,
            "next_agent": "project_manager"
        }
        workflow_steps.append(arch_output)
        self.history.append(arch_output)

        # Phase 3: Project Manager - Task Breakdown
        tasks = {
            "sprint_1": [
                "Setup project structure",
                "Implement core engine",
                "Create plugin interface"
            ],
            "sprint_2": [
                "Implement API layer",
                "Add authentication",
                "Create first plugins"
            ],
            "sprint_3": [
                "Testing",
                "Documentation",
                "Deployment"
            ]
        }
        self.project["deliverables"]["tasks"] = tasks

        pm_task_output = {
            "agent": "project_manager",
            "phase": "planning",
            "output": tasks,
            "next_agent": "engineer"
        }
        workflow_steps.append(pm_task_output)
        self.history.append(pm_task_output)

        # Phase 4: Engineer - Implementation
        code = {
            "files_created": 15,
            "lines_of_code": 1200,
            "modules": ["core", "api", "plugins"],
            "tests": "Unit tests implemented"
        }
        self.project["deliverables"]["code"] = code

        eng_output = {
            "agent": "engineer",
            "phase": "implementation",
            "output": code,
            "next_agent": "qa"
        }
        workflow_steps.append(eng_output)
        self.history.append(eng_output)

        # Phase 5: QA - Testing
        qa_report = {
            "tests_run": 45,
            "passed": 43,
            "failed": 2,
            "coverage": "87%",
            "issues": [
                "Minor: Edge case in plugin loader",
                "Minor: Documentation incomplete"
            ]
        }
        self.project["deliverables"]["qa_report"] = qa_report

        qa_output = {
            "agent": "qa",
            "phase": "testing",
            "output": qa_report,
            "next_agent": None
        }
        workflow_steps.append(qa_output)
        self.history.append(qa_output)

        self.project["status"] = "completed"

        return {
            "success": True,
            "workflow": workflow_steps,
            "total_steps": len(workflow_steps),
            "project_status": "completed",
            "deliverables": list(self.project["deliverables"].keys())
        }

    def _agent_communicate(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Enable communication between agents"""
        from_agent = params.get("from", "")
        to_agent = params.get("to", "")
        message = params.get("message", "")
        context = params.get("context", {})

        if from_agent not in self.agents:
            return {"success": False, "error": f"Agent {from_agent} not found"}

        if to_agent not in self.agents:
            return {"success": False, "error": f"Agent {to_agent} not found"}

        communication = {
            "from": from_agent,
            "to": to_agent,
            "message": message,
            "context": context,
            "timestamp": "now"
        }

        # Simulate agent response based on role
        to_role = self.agents[to_agent]["role"]
        response = f"[{to_role}] Acknowledged. "

        if "review" in message.lower():
            response += "I'll review and provide feedback."
        elif "implement" in message.lower():
            response += "I'll start implementation."
        elif "test" in message.lower():
            response += "I'll create test cases."
        else:
            response += "Understood."

        communication["response"] = response

        self.history.append(communication)

        return {
            "success": True,
            "communication": communication
        }

    def _get_deliverable(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Get a specific project deliverable"""
        deliverable_type = params.get("type", "")

        if not self.project:
            return {"success": False, "error": "No project exists"}

        if deliverable_type not in self.project["deliverables"]:
            return {"success": False, "error": f"Deliverable {deliverable_type} not found"}

        return {
            "success": True,
            "deliverable": self.project["deliverables"][deliverable_type],
            "type": deliverable_type
        }

    def _add_agent(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Add a custom agent role"""
        agent_id = params.get("id", "")
        role = params.get("role", "")
        responsibilities = params.get("responsibilities", [])

        if agent_id in self.agents:
            return {"success": False, "error": f"Agent {agent_id} already exists"}

        self.agents[agent_id] = {
            "role": role,
            "responsibilities": responsibilities,
            "active": True
        }

        return {
            "success": True,
            "agent_id": agent_id,
            "total_agents": len(self.agents)
        }

    def _get_project_status(self) -> Dict[str, Any]:
        """Get current project status"""
        if not self.project:
            return {"success": False, "error": "No project exists"}

        return {
            "success": True,
            "project": self.project,
            "active_agents": len([a for a in self.agents.values() if a["active"]]),
            "deliverables_completed": len(self.project["deliverables"]),
            "workflow_history": len(self.history)
        }

    def shutdown(self) -> bool:
        """Cleanup plugin resources"""
        self._initialized = False
        self.agents = {}
        self.project = None
        self.history = []
        return True
