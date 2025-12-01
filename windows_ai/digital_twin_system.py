"""
Digital Twin System

Creates a digital twin of the user's workflow environment for task simulation,
outcome prediction, and workflow optimization before execution.
"""

from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional
from datetime import datetime
from pathlib import Path
import json
import logging
import uuid

logger = logging.getLogger(__name__)


@dataclass
class DigitalEnvironment:
    """Digital twin environment"""
    env_id: str
    user_id: str
    applications: List[Dict[str, Any]]
    files: List[Dict[str, Any]]
    system_state: Dict[str, Any]
    network_state: Dict[str, Any]
    created_at: datetime = field(default_factory=datetime.now)


@dataclass
class TaskSimulation:
    """Simulated task execution"""
    simulation_id: str
    task_definition: Dict[str, Any]
    predicted_outcome: Dict[str, Any]
    potential_conflicts: List[str]
    optimization_suggestions: List[str]
    success_probability: float
    estimated_duration: float
    timestamp: datetime = field(default_factory=datetime.now)


class DigitalTwinSystem:
    """
    Digital Twin System

    Simulates user workflow environment for predictive task execution
    """

    def __init__(self, data_dir: Path):
        self.data_dir = Path(data_dir)
        self.data_dir.mkdir(parents=True, exist_ok=True)

        self.environments: Dict[str, DigitalEnvironment] = {}
        self.simulations: List[TaskSimulation] = []

        self._load_state()
        logger.info("Digital Twin System initialized")

    def create_environment(
        self,
        user_id: str,
        current_state: Dict[str, Any]
    ) -> DigitalEnvironment:
        """Create digital twin environment"""
        env = DigitalEnvironment(
            env_id=str(uuid.uuid4()),
            user_id=user_id,
            applications=current_state.get("applications", []),
            files=current_state.get("files", []),
            system_state=current_state.get("system", {}),
            network_state=current_state.get("network", {})
        )

        self.environments[env.env_id] = env
        self._save_state()

        logger.info(f"Created digital twin for user {user_id}")
        return env

    def simulate_task(
        self,
        env_id: str,
        task_definition: Dict[str, Any]
    ) -> TaskSimulation:
        """Simulate task execution in digital twin"""
        if env_id not in self.environments:
            raise ValueError(f"Environment {env_id} not found")

        env = self.environments[env_id]

        # Simulate task execution
        conflicts = self._detect_conflicts(env, task_definition)
        optimizations = self._generate_optimizations(env, task_definition)
        success_prob = self._calculate_success_probability(env, task_definition, conflicts)
        duration = self._estimate_duration(task_definition)

        predicted_outcome = {
            "will_succeed": success_prob > 0.7,
            "expected_result": "Task completed successfully" if success_prob > 0.7 else "Potential issues detected",
            "resource_usage": {
                "cpu": task_definition.get("complexity", 0.5) * 100,
                "memory": task_definition.get("data_size", 100) * 1.5,
                "disk": task_definition.get("file_operations", 0) * 50
            }
        }

        simulation = TaskSimulation(
            simulation_id=str(uuid.uuid4()),
            task_definition=task_definition,
            predicted_outcome=predicted_outcome,
            potential_conflicts=conflicts,
            optimization_suggestions=optimizations,
            success_probability=success_prob,
            estimated_duration=duration
        )

        self.simulations.append(simulation)
        self._save_state()

        logger.info(f"Simulated task with {success_prob:.2f} success probability")
        return simulation

    def update_environment(
        self,
        env_id: str,
        state_changes: Dict[str, Any]
    ) -> DigitalEnvironment:
        """Update digital twin environment"""
        if env_id not in self.environments:
            raise ValueError(f"Environment {env_id} not found")

        env = self.environments[env_id]

        if "applications" in state_changes:
            env.applications = state_changes["applications"]
        if "files" in state_changes:
            env.files = state_changes["files"]
        if "system" in state_changes:
            env.system_state = state_changes["system"]

        self._save_state()
        return env

    def _detect_conflicts(
        self,
        env: DigitalEnvironment,
        task: Dict[str, Any]
    ) -> List[str]:
        """Detect potential conflicts"""
        conflicts = []

        # Check resource conflicts
        required_memory = task.get("memory_required", 0)
        available_memory = env.system_state.get("available_memory", float('inf'))
        if required_memory > available_memory:
            conflicts.append(f"Insufficient memory: need {required_memory}MB, have {available_memory}MB")

        # Check file conflicts
        files_to_write = task.get("output_files", [])
        existing_files = [f["path"] for f in env.files]
        for file in files_to_write:
            if file in existing_files:
                conflicts.append(f"File conflict: {file} already exists")

        # Check application conflicts
        required_app = task.get("required_application")
        if required_app:
            running_apps = [a["name"] for a in env.applications]
            if required_app not in running_apps:
                conflicts.append(f"Required application not running: {required_app}")

        return conflicts

    def _generate_optimizations(
        self,
        env: DigitalEnvironment,
        task: Dict[str, Any]
    ) -> List[str]:
        """Generate optimization suggestions"""
        optimizations = []

        # Suggest parallel execution if possible
        if task.get("parallelizable", False):
            optimizations.append("Task can be parallelized across multiple cores")

        # Suggest caching
        if task.get("repetitive_operations", 0) > 3:
            optimizations.append("Consider caching intermediate results")

        # Suggest batch processing
        if task.get("item_count", 0) > 100:
            optimizations.append("Use batch processing for better performance")

        return optimizations

    def _calculate_success_probability(
        self,
        env: DigitalEnvironment,
        task: Dict[str, Any],
        conflicts: List[str]
    ) -> float:
        """Calculate task success probability"""
        base_probability = 0.9

        # Reduce probability for each conflict
        probability = base_probability - (len(conflicts) * 0.15)

        # Adjust for task complexity
        complexity = task.get("complexity", 0.5)
        probability *= (1.0 - complexity * 0.2)

        return max(0.0, min(1.0, probability))

    def _estimate_duration(self, task: Dict[str, Any]) -> float:
        """Estimate task duration in seconds"""
        base_duration = 10.0
        complexity_factor = task.get("complexity", 0.5)
        item_count = task.get("item_count", 1)

        duration = base_duration * (1 + complexity_factor) * (item_count ** 0.5)
        return duration

    def get_simulation_history(
        self,
        env_id: Optional[str] = None
    ) -> List[TaskSimulation]:
        """Get simulation history"""
        if env_id:
            env = self.environments.get(env_id)
            if env:
                return [s for s in self.simulations
                       if s.task_definition.get("env_id") == env_id]
        return self.simulations

    def _save_state(self):
        """Save state"""
        try:
            data = {
                "environments_count": len(self.environments),
                "simulations_count": len(self.simulations)
            }
            with open(self.data_dir / "digital_twin_state.json", "w") as f:
                json.dump(data, f, indent=2)
        except Exception as e:
            logger.error(f"Failed to save digital twin state: {e}")

    def _load_state(self):
        """Load state"""
        try:
            state_file = self.data_dir / "digital_twin_state.json"
            if state_file.exists():
                with open(state_file, "r") as f:
                    data = json.load(f)
                logger.info(f"Loaded {data.get('simulations_count', 0)} simulations")
        except Exception as e:
            logger.error(f"Failed to load digital twin state: {e}")


# Global instance
_digital_twin: Optional[DigitalTwinSystem] = None


def get_digital_twin() -> Optional[DigitalTwinSystem]:
    return _digital_twin


def initialize_digital_twin(data_dir: Path) -> DigitalTwinSystem:
    global _digital_twin
    _digital_twin = DigitalTwinSystem(data_dir)
    return _digital_twin
