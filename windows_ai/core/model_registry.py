"""
Model Registry — Track, version, and manage AI model deployments.
Supports model versioning, A/B testing, rollback, and performance monitoring.
"""
import logging
import time
import uuid
from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional, Tuple
from enum import Enum

logger = logging.getLogger(__name__)


class ModelStatus(Enum):
    REGISTERED = "registered"
    STAGING = "staging"
    PRODUCTION = "production"
    ARCHIVED = "archived"
    FAILED = "failed"


class ModelType(Enum):
    LLM = "llm"
    EMBEDDING = "embedding"
    CLASSIFICATION = "classification"
    GENERATION = "generation"
    DETECTION = "detection"
    TRANSCRIPTION = "transcription"
    TTS = "tts"
    CUSTOM = "custom"


@dataclass
class ModelVersion:
    version_id: str
    version: str
    model_path: str
    created_at: float
    status: ModelStatus = ModelStatus.REGISTERED
    metrics: Dict[str, float] = field(default_factory=dict)
    parameters: Dict[str, Any] = field(default_factory=dict)
    tags: List[str] = field(default_factory=list)
    description: str = ""
    size_bytes: int = 0
    checksum: str = ""


@dataclass
class ModelEntry:
    model_id: str
    name: str
    model_type: ModelType
    description: str = ""
    owner: str = ""
    versions: List[ModelVersion] = field(default_factory=list)
    current_version: Optional[str] = None
    created_at: float = field(default_factory=time.time)
    metadata: Dict[str, Any] = field(default_factory=dict)

    def get_version(self, version_id: str) -> Optional[ModelVersion]:
        for v in self.versions:
            if v.version_id == version_id or v.version == version_id:
                return v
        return None

    def get_production_version(self) -> Optional[ModelVersion]:
        for v in self.versions:
            if v.status == ModelStatus.PRODUCTION:
                return v
        return None

    def latest_version(self) -> Optional[ModelVersion]:
        if not self.versions:
            return None
        return max(self.versions, key=lambda v: v.created_at)


@dataclass
class ABTest:
    test_id: str
    name: str
    model_id: str
    version_a: str
    version_b: str
    traffic_split: float = 0.5  # fraction going to version_b
    started_at: float = field(default_factory=time.time)
    ended_at: Optional[float] = None
    results_a: Dict[str, float] = field(default_factory=dict)
    results_b: Dict[str, float] = field(default_factory=dict)
    total_requests_a: int = 0
    total_requests_b: int = 0
    is_active: bool = True

    def record_result(self, version: str, metrics: Dict[str, float]):
        if version == self.version_a:
            for k, v in metrics.items():
                self.results_a[k] = self.results_a.get(k, 0) + v
            self.total_requests_a += 1
        elif version == self.version_b:
            for k, v in metrics.items():
                self.results_b[k] = self.results_b.get(k, 0) + v
            self.total_requests_b += 1

    def get_winner(self, metric: str = "accuracy") -> Optional[str]:
        avg_a = self.results_a.get(metric, 0) / max(self.total_requests_a, 1)
        avg_b = self.results_b.get(metric, 0) / max(self.total_requests_b, 1)
        if self.total_requests_a < 10 or self.total_requests_b < 10:
            return None  # Not enough data
        return self.version_a if avg_a >= avg_b else self.version_b


class ModelPerformanceTracker:
    """Tracks model performance metrics over time."""

    def __init__(self):
        self._metrics: Dict[str, List[Dict[str, Any]]] = {}

    def record(self, model_id: str, version: str, metrics: Dict[str, float]):
        key = f"{model_id}:{version}"
        entry = {"timestamp": time.time(), **metrics}
        self._metrics.setdefault(key, []).append(entry)
        # Keep last 10000 entries
        if len(self._metrics[key]) > 10000:
            self._metrics[key] = self._metrics[key][-10000:]

    def get_stats(self, model_id: str, version: str, metric: str = "latency") -> Dict[str, float]:
        key = f"{model_id}:{version}"
        entries = self._metrics.get(key, [])
        values = [e.get(metric, 0) for e in entries if metric in e]
        if not values:
            return {"count": 0}
        values.sort()
        n = len(values)
        return {
            "count": n,
            "mean": sum(values) / n,
            "min": values[0],
            "max": values[-1],
            "p50": values[n // 2],
            "p95": values[int(n * 0.95)],
            "p99": values[int(n * 0.99)],
        }

    def detect_degradation(self, model_id: str, version: str, metric: str = "latency",
                           window: int = 100, threshold: float = 1.5) -> bool:
        key = f"{model_id}:{version}"
        entries = self._metrics.get(key, [])
        values = [e.get(metric, 0) for e in entries if metric in e]
        if len(values) < window * 2:
            return False
        recent = values[-window:]
        baseline = values[-window*2:-window]
        recent_avg = sum(recent) / len(recent)
        baseline_avg = sum(baseline) / len(baseline)
        return recent_avg > baseline_avg * threshold


class ModelRegistry:
    """Central registry for AI model management."""

    def __init__(self):
        self._models: Dict[str, ModelEntry] = {}
        self._ab_tests: Dict[str, ABTest] = {}
        self.performance = ModelPerformanceTracker()
        logger.info("ModelRegistry initialized")

    def register_model(self, name: str, model_type: ModelType, description: str = "",
                       owner: str = "", metadata: Dict[str, Any] = None) -> ModelEntry:
        model_id = str(uuid.uuid4())
        entry = ModelEntry(
            model_id=model_id, name=name, model_type=model_type,
            description=description, owner=owner, metadata=metadata or {}
        )
        self._models[model_id] = entry
        logger.info(f"Model registered: {name} ({model_id})")
        return entry

    def add_version(self, model_id: str, version: str, model_path: str,
                    metrics: Dict[str, float] = None, parameters: Dict[str, Any] = None,
                    tags: List[str] = None) -> Optional[ModelVersion]:
        model = self._models.get(model_id)
        if not model:
            logger.error(f"Model not found: {model_id}")
            return None
        ver = ModelVersion(
            version_id=str(uuid.uuid4()), version=version, model_path=model_path,
            created_at=time.time(), metrics=metrics or {}, parameters=parameters or {},
            tags=tags or []
        )
        model.versions.append(ver)
        logger.info(f"Version {version} added to model {model.name}")
        return ver

    def promote_version(self, model_id: str, version_id: str, target: ModelStatus) -> bool:
        model = self._models.get(model_id)
        if not model:
            return False
        version = model.get_version(version_id)
        if not version:
            return False
        # Demote current production if promoting to production
        if target == ModelStatus.PRODUCTION:
            for v in model.versions:
                if v.status == ModelStatus.PRODUCTION:
                    v.status = ModelStatus.ARCHIVED
            model.current_version = version_id
        version.status = target
        logger.info(f"Version {version.version} promoted to {target.value}")
        return True

    def rollback(self, model_id: str) -> Optional[ModelVersion]:
        model = self._models.get(model_id)
        if not model:
            return None
        archived = [v for v in model.versions if v.status == ModelStatus.ARCHIVED]
        if not archived:
            return None
        latest_archived = max(archived, key=lambda v: v.created_at)
        # Demote current production
        for v in model.versions:
            if v.status == ModelStatus.PRODUCTION:
                v.status = ModelStatus.STAGING
        latest_archived.status = ModelStatus.PRODUCTION
        model.current_version = latest_archived.version_id
        logger.info(f"Rolled back to version {latest_archived.version}")
        return latest_archived

    def create_ab_test(self, model_id: str, version_a: str, version_b: str,
                       traffic_split: float = 0.5) -> Optional[ABTest]:
        model = self._models.get(model_id)
        if not model:
            return None
        test = ABTest(
            test_id=str(uuid.uuid4()), name=f"AB_{model.name}",
            model_id=model_id, version_a=version_a, version_b=version_b,
            traffic_split=traffic_split
        )
        self._ab_tests[test.test_id] = test
        logger.info(f"A/B test created: {version_a} vs {version_b}")
        return test

    def route_request(self, test_id: str) -> Optional[str]:
        test = self._ab_tests.get(test_id)
        if not test or not test.is_active:
            return None
        import random
        return test.version_b if random.random() < test.traffic_split else test.version_a

    def get_model(self, model_id: str) -> Optional[ModelEntry]:
        return self._models.get(model_id)

    def search_models(self, query: str = "", model_type: ModelType = None,
                      status: ModelStatus = None) -> List[ModelEntry]:
        results = []
        for model in self._models.values():
            if query and query.lower() not in model.name.lower() and query.lower() not in model.description.lower():
                continue
            if model_type and model.model_type != model_type:
                continue
            if status:
                has_status = any(v.status == status for v in model.versions)
                if not has_status:
                    continue
            results.append(model)
        return results

    def list_models(self) -> List[Dict[str, Any]]:
        return [
            {
                "model_id": m.model_id, "name": m.name, "type": m.model_type.value,
                "versions": len(m.versions), "current_version": m.current_version,
                "production": m.get_production_version() is not None,
            }
            for m in self._models.values()
        ]

    def get_stats(self) -> Dict[str, Any]:
        total_models = len(self._models)
        total_versions = sum(len(m.versions) for m in self._models.values())
        production = sum(1 for m in self._models.values() if m.get_production_version())
        return {
            "total_models": total_models,
            "total_versions": total_versions,
            "production_models": production,
            "active_ab_tests": sum(1 for t in self._ab_tests.values() if t.is_active),
        }


# Global instance
_registry: Optional[ModelRegistry] = None

def get_model_registry() -> ModelRegistry:
    global _registry
    if _registry is None:
        _registry = ModelRegistry()
    return _registry
