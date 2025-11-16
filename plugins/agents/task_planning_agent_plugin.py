"""
Task Planning Agent Plugin
AI agent specialized in breaking down and planning complex tasks
"""

from typing import Dict, Any, Optional, List
from collections import deque


class TaskPlanningAgentPlugin:
    """Plugin for task planning and decomposition agent"""

    name = "task_planning_agent"
    version = "1.0.0"
    description = "AI agent that plans and breaks down complex tasks"
    author = "Windows AI Team"

    def __init__(self):
        self.plans = {}
        self.tasks = {}
        self.dependencies = {}
        self._initialized = False

    def initialize(self, config: Optional[Dict[str, Any]] = None) -> bool:
        """Initialize the Task Planning Agent plugin"""
        try:
            self._initialized = True
            return True
        except Exception as e:
            print(f"Error initializing Task Planning Agent plugin: {e}")
            return False

    def execute(self, action: str, params: Dict[str, Any]) -> Dict[str, Any]:
        """Execute a Task Planning Agent action"""
        if not self._initialized:
            return {"success": False, "error": "Plugin not initialized"}

        try:
            if action == "create_plan":
                return self._create_plan(params)
            elif action == "decompose_task":
                return self._decompose_task(params)
            elif action == "add_dependency":
                return self._add_dependency(params)
            elif action == "get_execution_order":
                return self._get_execution_order(params)
            elif action == "estimate_time":
                return self._estimate_time(params)
            elif action == "identify_risks":
                return self._identify_risks(params)
            elif action == "optimize_plan":
                return self._optimize_plan(params)
            elif action == "validate_plan":
                return self._validate_plan(params)
            else:
                return {"success": False, "error": f"Unknown action: {action}"}
        except Exception as e:
            return {"success": False, "error": str(e)}

    def _create_plan(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Create a plan for achieving a goal"""
        goal = params.get("goal", "")
        context = params.get("context", {})
        constraints = params.get("constraints", [])

        plan_id = f"plan_{len(self.plans)}"

        # Analyze goal and create initial plan structure
        plan = {
            "id": plan_id,
            "goal": goal,
            "context": context,
            "constraints": constraints,
            "phases": [],
            "tasks": [],
            "status": "draft",
            "created_at": "now"
        }

        # Identify major phases
        phases = self._identify_phases(goal, context)
        plan["phases"] = phases

        # Create tasks for each phase
        all_tasks = []
        for i, phase in enumerate(phases):
            phase_tasks = self._generate_phase_tasks(phase, i)
            all_tasks.extend(phase_tasks)

        plan["tasks"] = all_tasks

        self.plans[plan_id] = plan

        return {
            "success": True,
            "plan_id": plan_id,
            "plan": plan,
            "num_phases": len(phases),
            "num_tasks": len(all_tasks)
        }

    def _identify_phases(self, goal: str, context: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Identify major phases of a project"""
        # Standard project phases (simplified)
        phases = [
            {
                "id": "planning",
                "name": "Planning & Analysis",
                "description": "Define requirements and plan approach",
                "order": 1
            },
            {
                "id": "design",
                "name": "Design",
                "description": "Design solution architecture",
                "order": 2
            },
            {
                "id": "implementation",
                "name": "Implementation",
                "description": "Build the solution",
                "order": 3
            },
            {
                "id": "testing",
                "name": "Testing & QA",
                "description": "Test and validate solution",
                "order": 4
            },
            {
                "id": "deployment",
                "name": "Deployment",
                "description": "Deploy and monitor solution",
                "order": 5
            }
        ]

        return phases

    def _generate_phase_tasks(self, phase: Dict[str, Any], phase_index: int) -> List[Dict[str, Any]]:
        """Generate tasks for a specific phase"""
        tasks = []
        phase_id = phase["id"]

        # Generate 2-4 tasks per phase
        if phase_id == "planning":
            task_names = [
                "Gather requirements",
                "Define scope",
                "Identify stakeholders",
                "Create timeline"
            ]
        elif phase_id == "design":
            task_names = [
                "Design architecture",
                "Create mockups/wireframes",
                "Define data models"
            ]
        elif phase_id == "implementation":
            task_names = [
                "Setup development environment",
                "Implement core features",
                "Implement additional features",
                "Code review"
            ]
        elif phase_id == "testing":
            task_names = [
                "Unit testing",
                "Integration testing",
                "User acceptance testing"
            ]
        elif phase_id == "deployment":
            task_names = [
                "Prepare deployment",
                "Deploy to production",
                "Monitor and validate"
            ]
        else:
            task_names = ["Complete phase tasks"]

        for i, name in enumerate(task_names):
            task = {
                "id": f"task_{phase_index}_{i}",
                "name": name,
                "phase": phase_id,
                "status": "pending",
                "priority": "medium",
                "estimated_hours": 4 + i * 2
            }
            tasks.append(task)

        return tasks

    def _decompose_task(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Decompose a complex task into subtasks"""
        task_description = params.get("task", "")
        max_subtasks = params.get("max_subtasks", 5)
        task_id = params.get("task_id", f"task_{len(self.tasks)}")

        # Analyze task complexity
        complexity = self._assess_complexity(task_description)

        # Generate subtasks
        subtasks = []
        num_subtasks = min(complexity["complexity_level"], max_subtasks)

        for i in range(num_subtasks):
            subtask = {
                "id": f"{task_id}_sub_{i}",
                "parent_task": task_id,
                "name": f"Subtask {i+1}: {task_description[:30]}...",
                "status": "pending",
                "order": i + 1
            }
            subtasks.append(subtask)

        task = {
            "id": task_id,
            "description": task_description,
            "subtasks": subtasks,
            "complexity": complexity,
            "status": "decomposed"
        }

        self.tasks[task_id] = task

        return {
            "success": True,
            "task_id": task_id,
            "task": task,
            "num_subtasks": len(subtasks),
            "complexity": complexity["complexity_level"]
        }

    def _assess_complexity(self, task_description: str) -> Dict[str, Any]:
        """Assess task complexity"""
        # Simple heuristic-based complexity assessment
        complexity_level = 1

        # Longer descriptions usually mean more complex tasks
        word_count = len(task_description.split())
        if word_count > 50:
            complexity_level += 2
        elif word_count > 20:
            complexity_level += 1

        # Multiple requirements increase complexity
        if any(word in task_description.lower() for word in ["and", "also", "additionally"]):
            complexity_level += 1

        # Technical terms indicate complexity
        technical_terms = ["implement", "integrate", "optimize", "refactor", "design"]
        if any(term in task_description.lower() for term in technical_terms):
            complexity_level += 1

        complexity_level = min(complexity_level, 5)

        return {
            "complexity_level": complexity_level,
            "word_count": word_count,
            "description": ["Very Simple", "Simple", "Moderate", "Complex", "Very Complex"][complexity_level - 1]
        }

    def _add_dependency(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Add a dependency between tasks"""
        task_id = params.get("task_id", "")
        depends_on = params.get("depends_on", "")
        dependency_type = params.get("type", "finish_to_start")  # finish_to_start, start_to_start

        if task_id not in self.dependencies:
            self.dependencies[task_id] = []

        dependency = {
            "depends_on": depends_on,
            "type": dependency_type
        }

        self.dependencies[task_id].append(dependency)

        return {
            "success": True,
            "task_id": task_id,
            "depends_on": depends_on,
            "dependency_type": dependency_type,
            "total_dependencies": len(self.dependencies[task_id])
        }

    def _get_execution_order(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Get optimal execution order considering dependencies"""
        plan_id = params.get("plan_id", "")

        if plan_id not in self.plans:
            return {"success": False, "error": f"Plan {plan_id} not found"}

        plan = self.plans[plan_id]
        tasks = plan["tasks"]

        # Topological sort for task ordering
        execution_order = self._topological_sort(tasks)

        # Group by phase
        phase_groups = {}
        for task in execution_order:
            phase = task.get("phase", "unknown")
            if phase not in phase_groups:
                phase_groups[phase] = []
            phase_groups[phase].append(task)

        return {
            "success": True,
            "plan_id": plan_id,
            "execution_order": execution_order,
            "phase_groups": phase_groups,
            "total_tasks": len(execution_order)
        }

    def _topological_sort(self, tasks: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Topological sort considering dependencies"""
        # Simple ordering by phase and task order
        # In production, would use proper topological sort with dependency graph
        sorted_tasks = sorted(tasks, key=lambda t: (
            self._get_phase_order(t.get("phase", "unknown")),
            t.get("id", "")
        ))

        return sorted_tasks

    def _get_phase_order(self, phase: str) -> int:
        """Get numeric order for phase"""
        phase_order = {
            "planning": 1,
            "design": 2,
            "implementation": 3,
            "testing": 4,
            "deployment": 5
        }
        return phase_order.get(phase, 99)

    def _estimate_time(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Estimate time required for plan completion"""
        plan_id = params.get("plan_id", "")
        team_size = params.get("team_size", 1)
        work_hours_per_day = params.get("work_hours_per_day", 6)

        if plan_id not in self.plans:
            return {"success": False, "error": f"Plan {plan_id} not found"}

        plan = self.plans[plan_id]
        tasks = plan["tasks"]

        # Calculate total estimated hours
        total_hours = sum(task.get("estimated_hours", 8) for task in tasks)

        # Account for team size (with diminishing returns)
        team_factor = 1.0 / (team_size ** 0.7) if team_size > 1 else 1.0
        adjusted_hours = total_hours * team_factor

        # Calculate days
        days = adjusted_hours / work_hours_per_day

        # Add buffer for unknowns (20%)
        buffered_days = days * 1.2

        return {
            "success": True,
            "plan_id": plan_id,
            "estimates": {
                "total_task_hours": total_hours,
                "adjusted_hours": round(adjusted_hours, 1),
                "estimated_days": round(days, 1),
                "buffered_days": round(buffered_days, 1),
                "team_size": team_size,
                "work_hours_per_day": work_hours_per_day
            }
        }

    def _identify_risks(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Identify potential risks in the plan"""
        plan_id = params.get("plan_id", "")

        if plan_id not in self.plans:
            return {"success": False, "error": f"Plan {plan_id} not found"}

        plan = self.plans[plan_id]

        # Identify common project risks
        risks = [
            {
                "id": "risk_1",
                "category": "scope",
                "description": "Scope creep during implementation",
                "likelihood": "medium",
                "impact": "high",
                "mitigation": "Regular scope reviews and change control"
            },
            {
                "id": "risk_2",
                "category": "technical",
                "description": "Technical challenges in implementation",
                "likelihood": "medium",
                "impact": "medium",
                "mitigation": "Proof of concepts for complex features"
            },
            {
                "id": "risk_3",
                "category": "resource",
                "description": "Key team members unavailable",
                "likelihood": "low",
                "impact": "high",
                "mitigation": "Cross-training and documentation"
            },
            {
                "id": "risk_4",
                "category": "dependency",
                "description": "External dependencies delayed",
                "likelihood": "medium",
                "impact": "medium",
                "mitigation": "Identify alternatives and buffers"
            }
        ]

        # Calculate risk scores
        likelihood_scores = {"low": 1, "medium": 2, "high": 3}
        impact_scores = {"low": 1, "medium": 2, "high": 3}

        for risk in risks:
            risk["score"] = likelihood_scores[risk["likelihood"]] * impact_scores[risk["impact"]]

        # Sort by score
        risks.sort(key=lambda r: r["score"], reverse=True)

        return {
            "success": True,
            "plan_id": plan_id,
            "risks": risks,
            "num_risks": len(risks),
            "high_priority_risks": [r for r in risks if r["score"] >= 6]
        }

    def _optimize_plan(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Optimize plan for time, cost, or quality"""
        plan_id = params.get("plan_id", "")
        optimization_goal = params.get("goal", "time")  # time, cost, quality

        if plan_id not in self.plans:
            return {"success": False, "error": f"Plan {plan_id} not found"}

        plan = self.plans[plan_id]
        tasks = plan["tasks"]

        optimizations = []

        if optimization_goal == "time":
            # Suggest parallelization
            optimizations.append({
                "type": "parallelization",
                "description": "Run independent tasks in parallel",
                "impact": "20-30% time reduction"
            })

            # Suggest removing non-critical tasks
            optimizations.append({
                "type": "scope_reduction",
                "description": "Defer low-priority features to later phases",
                "impact": "15-20% time reduction"
            })

        elif optimization_goal == "cost":
            optimizations.append({
                "type": "resource_optimization",
                "description": "Use existing tools instead of custom development",
                "impact": "30-40% cost reduction"
            })

        elif optimization_goal == "quality":
            optimizations.append({
                "type": "additional_review",
                "description": "Add code review and QA checkpoints",
                "impact": "50% defect reduction"
            })

        return {
            "success": True,
            "plan_id": plan_id,
            "optimization_goal": optimization_goal,
            "optimizations": optimizations,
            "num_optimizations": len(optimizations)
        }

    def _validate_plan(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Validate plan completeness and feasibility"""
        plan_id = params.get("plan_id", "")

        if plan_id not in self.plans:
            return {"success": False, "error": f"Plan {plan_id} not found"}

        plan = self.plans[plan_id]

        validation_results = {
            "is_valid": True,
            "issues": [],
            "warnings": []
        }

        # Check if plan has tasks
        if not plan["tasks"]:
            validation_results["is_valid"] = False
            validation_results["issues"].append("Plan has no tasks")

        # Check if all phases are covered
        phases_present = set(task["phase"] for task in plan["tasks"])
        if len(phases_present) < 3:
            validation_results["warnings"].append("Plan covers fewer than 3 phases")

        # Check task distribution
        if len(plan["tasks"]) < 5:
            validation_results["warnings"].append("Very few tasks - plan may be too high-level")

        return {
            "success": True,
            "plan_id": plan_id,
            "validation": validation_results
        }

    def shutdown(self) -> bool:
        """Cleanup plugin resources"""
        self._initialized = False
        self.plans = {}
        self.tasks = {}
        self.dependencies = {}
        return True
