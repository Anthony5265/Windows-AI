"""Active Learning System"""
from dataclasses import dataclass
from typing import List, Dict, Any, Optional
import logging
logger = logging.getLogger(__name__)

@dataclass
class LabelRequest:
    sample_id: str
    data: Any
    uncertainty: float
    priority: float

class ActiveLearningSystem:
    def __init__(self, data_dir):
        self.data_dir = data_dir
        self.data_dir.mkdir(parents=True, exist_ok=True)
        self.label_requests: List[LabelRequest] = []
        logger.info("Active Learning System initialized")

    def select_samples(self, unlabeled_data: List[Any], n_samples: int = 10) -> List[LabelRequest]:
        import uuid, random
        requests = []
        for i, data in enumerate(unlabeled_data[:n_samples]):
            requests.append(LabelRequest(str(uuid.uuid4()), data, random.random(), random.random()))
        self.label_requests.extend(requests)
        return sorted(requests, key=lambda r: r.uncertainty, reverse=True)

_active_learning: Optional[ActiveLearningSystem] = None
def get_active_learning() -> Optional[ActiveLearningSystem]: return _active_learning
def initialize_active_learning(data_dir) -> ActiveLearningSystem:
    global _active_learning
    _active_learning = ActiveLearningSystem(data_dir)
    return _active_learning
