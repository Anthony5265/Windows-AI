"""
Federated Learning System

Enables distributed machine learning across multiple devices while preserving privacy.
Aggregates model updates without sharing raw data.
"""

from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional
from datetime import datetime
from pathlib import Path
import json
import logging
from enum import Enum
import hashlib

logger = logging.getLogger(__name__)


class AggregationStrategy(Enum):
    """Model aggregation strategies"""
    FEDAVG = "federated_averaging"
    FEDPROX = "federated_proximal"
    FEDADAM = "federated_adam"
    WEIGHTED = "weighted_average"


@dataclass
class ClientDevice:
    """Federated learning client device"""
    client_id: str
    device_name: str
    compute_capability: float  # 0-1 scale
    data_size: int
    last_update: datetime
    model_version: int
    is_active: bool = True


@dataclass
class ModelUpdate:
    """Model update from client"""
    update_id: str
    client_id: str
    model_version: int
    parameters: Dict[str, Any]  # Model weights/gradients
    metrics: Dict[str, float]
    data_samples: int
    timestamp: datetime = field(default_factory=datetime.now)


@dataclass
class GlobalModel:
    """Global federated model"""
    model_id: str
    version: int
    parameters: Dict[str, Any]
    performance_metrics: Dict[str, float]
    num_clients: int
    total_samples: int
    last_updated: datetime


@dataclass
class FederatedRound:
    """Training round in federated learning"""
    round_id: int
    participating_clients: List[str]
    updates_received: int
    global_model_version: int
    avg_performance: Dict[str, float]
    timestamp: datetime = field(default_factory=datetime.now)


class FederatedLearningSystem:
    """
    Federated Learning System

    Coordinates distributed training across multiple clients
    """

    def __init__(self, data_dir: Path):
        self.data_dir = Path(data_dir)
        self.data_dir.mkdir(parents=True, exist_ok=True)

        self.clients: Dict[str, ClientDevice] = {}
        self.global_model: Optional[GlobalModel] = None
        self.pending_updates: List[ModelUpdate] = []
        self.training_rounds: List[FederatedRound] = []
        self.current_round = 0

        self._load_state()
        logger.info("Federated Learning system initialized")

    def register_client(
        self,
        device_name: str,
        compute_capability: float,
        data_size: int
    ) -> ClientDevice:
        """Register new federated learning client"""
        import uuid

        client = ClientDevice(
            client_id=str(uuid.uuid4()),
            device_name=device_name,
            compute_capability=compute_capability,
            data_size=data_size,
            last_update=datetime.now(),
            model_version=0
        )

        self.clients[client.client_id] = client
        self._save_state()

        logger.info(f"Registered client: {device_name} ({client.client_id})")
        return client

    def initialize_global_model(self, initial_parameters: Dict[str, Any]) -> GlobalModel:
        """Initialize global model"""
        import uuid

        self.global_model = GlobalModel(
            model_id=str(uuid.uuid4()),
            version=1,
            parameters=initial_parameters,
            performance_metrics={},
            num_clients=0,
            total_samples=0,
            last_updated=datetime.now()
        )

        self._save_state()
        logger.info("Initialized global model")
        return self.global_model

    def select_clients_for_round(
        self,
        num_clients: int,
        min_data_size: int = 100
    ) -> List[ClientDevice]:
        """Select clients for training round"""
        import random

        # Filter active clients with sufficient data
        eligible = [
            c for c in self.clients.values()
            if c.is_active and c.data_size >= min_data_size
        ]

        if len(eligible) <= num_clients:
            return eligible

        # Weighted random selection based on data size
        weights = [c.data_size for c in eligible]
        total_weight = sum(weights)
        probabilities = [w / total_weight for w in weights]

        selected_indices = random.choices(
            range(len(eligible)),
            weights=probabilities,
            k=num_clients
        )

        return [eligible[i] for i in selected_indices]

    def submit_model_update(
        self,
        client_id: str,
        parameters: Dict[str, Any],
        metrics: Dict[str, float],
        data_samples: int
    ) -> ModelUpdate:
        """Submit model update from client"""
        import uuid

        update = ModelUpdate(
            update_id=str(uuid.uuid4()),
            client_id=client_id,
            model_version=self.global_model.version if self.global_model else 0,
            parameters=parameters,
            metrics=metrics,
            data_samples=data_samples
        )

        self.pending_updates.append(update)

        # Update client info
        if client_id in self.clients:
            self.clients[client_id].last_update = datetime.now()
            self.clients[client_id].model_version = update.model_version

        logger.info(f"Received update from client {client_id}")
        return update

    def aggregate_updates(
        self,
        strategy: AggregationStrategy = AggregationStrategy.FEDAVG
    ) -> GlobalModel:
        """Aggregate client updates into global model"""
        if not self.pending_updates or not self.global_model:
            return self.global_model

        if strategy == AggregationStrategy.FEDAVG:
            # Federated Averaging
            aggregated_params = {}
            total_samples = sum(u.data_samples for u in self.pending_updates)

            # Weight by number of samples
            for update in self.pending_updates:
                weight = update.data_samples / total_samples
                for key, value in update.parameters.items():
                    if key not in aggregated_params:
                        aggregated_params[key] = 0
                    # Simulated weighted average
                    aggregated_params[key] += weight * hash(str(value))

            # Update global model
            self.global_model.parameters = aggregated_params
            self.global_model.version += 1
            self.global_model.num_clients = len(self.pending_updates)
            self.global_model.total_samples = total_samples
            self.global_model.last_updated = datetime.now()

            # Calculate average metrics
            avg_metrics = {}
            for metric_name in self.pending_updates[0].metrics.keys():
                avg_metrics[metric_name] = sum(
                    u.metrics.get(metric_name, 0) for u in self.pending_updates
                ) / len(self.pending_updates)

            self.global_model.performance_metrics = avg_metrics

        # Record training round
        round_record = FederatedRound(
            round_id=self.current_round,
            participating_clients=[u.client_id for u in self.pending_updates],
            updates_received=len(self.pending_updates),
            global_model_version=self.global_model.version,
            avg_performance=self.global_model.performance_metrics
        )
        self.training_rounds.append(round_record)

        # Clear pending updates
        self.pending_updates.clear()
        self.current_round += 1

        self._save_state()
        logger.info(f"Aggregated {self.global_model.num_clients} updates (round {self.current_round})")

        return self.global_model

    def get_global_model_for_client(self, client_id: str) -> Optional[Dict[str, Any]]:
        """Get global model parameters for client"""
        if not self.global_model:
            return None

        if client_id not in self.clients:
            logger.warning(f"Unknown client: {client_id}")
            return None

        return {
            "model_id": self.global_model.model_id,
            "version": self.global_model.version,
            "parameters": self.global_model.parameters
        }

    def get_training_statistics(self) -> Dict[str, Any]:
        """Get federated learning statistics"""
        if not self.training_rounds:
            return {}

        return {
            "total_rounds": len(self.training_rounds),
            "total_clients": len(self.clients),
            "active_clients": sum(1 for c in self.clients.values() if c.is_active),
            "current_model_version": self.global_model.version if self.global_model else 0,
            "latest_performance": self.global_model.performance_metrics if self.global_model else {},
            "total_samples": self.global_model.total_samples if self.global_model else 0
        }

    def _save_state(self):
        """Save state to disk"""
        try:
            data = {
                "clients": {k: {
                    "client_id": v.client_id,
                    "device_name": v.device_name,
                    "compute_capability": v.compute_capability,
                    "data_size": v.data_size,
                    "model_version": v.model_version,
                    "is_active": v.is_active,
                    "last_update": v.last_update.isoformat()
                } for k, v in self.clients.items()},
                "current_round": self.current_round,
                "total_rounds": len(self.training_rounds)
            }

            with open(self.data_dir / "fl_state.json", "w") as f:
                json.dump(data, f, indent=2)
        except Exception as e:
            logger.error(f"Failed to save FL state: {e}")

    def _load_state(self):
        """Load state from disk"""
        try:
            state_file = self.data_dir / "fl_state.json"
            if state_file.exists():
                with open(state_file, "r") as f:
                    data = json.load(f)
                self.current_round = data.get("current_round", 0)
                logger.info(f"Loaded {len(data.get('clients', {}))} FL clients")
        except Exception as e:
            logger.error(f"Failed to load FL state: {e}")


# Global instance
_fl_system: Optional[FederatedLearningSystem] = None


def get_fl_system() -> Optional[FederatedLearningSystem]:
    """Get global FL system instance"""
    return _fl_system


def initialize_fl_system(data_dir: Path) -> FederatedLearningSystem:
    """Initialize FL system"""
    global _fl_system
    _fl_system = FederatedLearningSystem(data_dir)
    return _fl_system
