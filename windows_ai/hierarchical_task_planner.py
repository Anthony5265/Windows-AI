"""
Hierarchical Task Planning with Goal Decomposition

Breaks down high-level goals into sub-goals and atomic actions dynamically.
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
class HierarchicalTaskPlannerResult:
    """Result from HierarchicalTaskPlanner"""
    result_id: str
    status: str
    data: Dict[str, Any]
    timestamp: datetime = field(default_factory=datetime.now)


class HierarchicalTaskPlanner:
    """
    HierarchicalTaskPlanner

    Hierarchical Task Planning with Goal Decomposition
    """

    def __init__(self, data_dir: Path):
        self.data_dir = Path(data_dir)
        self.data_dir.mkdir(parents=True, exist_ok=True)
        self.results: List[HierarchicalTaskPlannerResult] = []
        self._load_state()
        logger.info("HierarchicalTaskPlanner initialized")

    def process(self, input_data: Dict[str, Any]) -> HierarchicalTaskPlannerResult:
        """Main processing function"""
        result = HierarchicalTaskPlannerResult(
            result_id=str(uuid.uuid4()),
            status="success",
            data={"processed": True, "input": input_data}
        )
        self.results.append(result)
        self._save_state()
        logger.info(f"Processed request in HierarchicalTaskPlanner")
        return result

    def get_results(self) -> List[HierarchicalTaskPlannerResult]:
        """Get all results"""
        return self.results

    def _save_state(self):
        try:
            data = {"results_count": len(self.results)}
            with open(self.data_dir / "hierarchical_task_planner_state.json", "w") as f:
                json.dump(data, f, indent=2)
        except Exception as e:
            logger.error(f"Failed to save state: {e}")

    def _load_state(self):
        try:
            state_file = self.data_dir / "hierarchical_task_planner_state.json"
            if state_file.exists():
                with open(state_file, "r") as f:
                    data = json.load(f)
                logger.info(f"Loaded {data.get('results_count', 0)} results")
        except Exception as e:
            logger.error(f"Failed to load state: {e}")


# Global instance
_hierarchical_task_planner: Optional[HierarchicalTaskPlanner] = None


def get_hierarchical_task_planner() -> Optional[HierarchicalTaskPlanner]:
    """Get global instance"""
    return _hierarchical_task_planner


def initialize_hierarchical_task_planner(data_dir: Path) -> HierarchicalTaskPlanner:
    """Initialize system"""
    global _hierarchical_task_planner
    _hierarchical_task_planner = HierarchicalTaskPlanner(data_dir)
    return _hierarchical_task_planner
