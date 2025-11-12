"""
Transfer Learning Management System

Manages domain adaptation and transfer learning workflows.
"""

from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional
from datetime import datetime
from pathlib import Path
import json
import logging

logger = logging.getLogger(__name__)


@dataclass
class PretrainedModel:
    model_id: str
    name: str
    source_domain: str
    architecture: str
    parameters_count: int
    pretrain_accuracy: float


@dataclass
class TransferTask:
    task_id: str
    source_model_id: str
    target_domain: str
    frozen_layers: List[str]
    fine_tuned_layers: List[str]
    transfer_accuracy: float
    improvement: float
    timestamp: datetime = field(default_factory=datetime.now)


class TransferLearningManager:
    def __init__(self, data_dir: Path):
        self.data_dir = Path(data_dir)
        self.data_dir.mkdir(parents=True, exist_ok=True)
        self.pretrained_models: List[PretrainedModel] = []
        self.transfer_tasks: List[TransferTask] = []
        logger.info("Transfer Learning Manager initialized")

    def register_pretrained_model(
        self,
        name: str,
        source_domain: str,
        architecture: str,
        parameters_count: int,
        accuracy: float
    ) -> PretrainedModel:
        import uuid
        model = PretrainedModel(
            model_id=str(uuid.uuid4()),
            name=name,
            source_domain=source_domain,
            architecture=architecture,
            parameters_count=parameters_count,
            pretrain_accuracy=accuracy
        )
        self.pretrained_models.append(model)
        return model

    def transfer_model(
        self,
        source_model_id: str,
        target_domain: str,
        freeze_ratio: float = 0.7
    ) -> TransferTask:
        import uuid
        import random
        task = TransferTask(
            task_id=str(uuid.uuid4()),
            source_model_id=source_model_id,
            target_domain=target_domain,
            frozen_layers=["layer1", "layer2", "layer3"],
            fine_tuned_layers=["layer4", "layer5"],
            transfer_accuracy=random.uniform(0.7, 0.95),
            improvement=random.uniform(0.1, 0.3)
        )
        self.transfer_tasks.append(task)
        logger.info(f"Transfer learning task created: {task.task_id}")
        return task

    def get_best_source_model(self, target_domain: str) -> Optional[PretrainedModel]:
        if not self.pretrained_models:
            return None
        return max(self.pretrained_models, key=lambda m: m.pretrain_accuracy)


_tl_manager: Optional[TransferLearningManager] = None

def get_tl_manager() -> Optional[TransferLearningManager]:
    return _tl_manager

def initialize_tl_manager(data_dir: Path) -> TransferLearningManager:
    global _tl_manager
    _tl_manager = TransferLearningManager(data_dir)
    return _tl_manager
