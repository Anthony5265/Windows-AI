"""On-Device Fine-Tuning Pipeline.

Provides a local fine-tuning workflow so users can customize AI models
without sending data to the cloud. Supports LoRA/QLoRA for efficient
parameter-efficient fine-tuning.
"""

from __future__ import annotations

import asyncio
import json
import logging
import os
import time
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional

logger = logging.getLogger(__name__)


class FineTuneMethod(str, Enum):
    """Supported fine-tuning methods."""
    FULL = "full"
    LORA = "lora"
    QLORA = "qlora"
    ADAPTER = "adapter"
    PREFIX_TUNING = "prefix_tuning"


class FineTuneStatus(str, Enum):
    """Fine-tune job status."""
    PENDING = "pending"
    PREPARING = "preparing"
    TRAINING = "training"
    EVALUATING = "evaluating"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


@dataclass
class FineTuneConfig:
    """Configuration for a fine-tuning job."""
    model_name: str
    method: FineTuneMethod = FineTuneMethod.LORA
    dataset_path: Optional[str] = None
    output_dir: str = "~/.windows_ai/fine_tuned/"
    learning_rate: float = 2e-5
    epochs: int = 3
    batch_size: int = 4
    max_seq_length: int = 512
    lora_rank: int = 16
    lora_alpha: int = 32
    lora_dropout: float = 0.05
    warmup_steps: int = 100
    save_steps: int = 500
    eval_steps: int = 100
    gradient_accumulation_steps: int = 1
    fp16: bool = True
    quantization_bits: Optional[int] = None  # 4 or 8 for QLoRA

    def to_dict(self) -> Dict[str, Any]:
        return {
            "model_name": self.model_name,
            "method": self.method.value,
            "dataset_path": self.dataset_path,
            "output_dir": self.output_dir,
            "learning_rate": self.learning_rate,
            "epochs": self.epochs,
            "batch_size": self.batch_size,
            "max_seq_length": self.max_seq_length,
            "lora_rank": self.lora_rank,
            "lora_alpha": self.lora_alpha,
            "fp16": self.fp16,
        }


@dataclass
class FineTuneJob:
    """Represents an active or completed fine-tuning job."""
    job_id: str
    config: FineTuneConfig
    status: FineTuneStatus = FineTuneStatus.PENDING
    progress: float = 0.0  # 0.0 to 1.0
    current_epoch: int = 0
    current_step: int = 0
    total_steps: int = 0
    train_loss: float = 0.0
    eval_loss: Optional[float] = None
    started_at: Optional[float] = None
    completed_at: Optional[float] = None
    error: Optional[str] = None
    metrics: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "job_id": self.job_id,
            "status": self.status.value,
            "model": self.config.model_name,
            "method": self.config.method.value,
            "progress": round(self.progress * 100, 1),
            "current_epoch": self.current_epoch,
            "current_step": self.current_step,
            "total_steps": self.total_steps,
            "train_loss": round(self.train_loss, 4),
            "eval_loss": round(self.eval_loss, 4) if self.eval_loss else None,
            "error": self.error,
            "metrics": self.metrics,
        }


class DatasetValidator:
    """Validates and prepares datasets for fine-tuning."""

    SUPPORTED_FORMATS = {".json", ".jsonl", ".csv", ".parquet", ".txt"}

    def validate(self, path: str) -> Dict[str, Any]:
        """Validate a dataset file."""
        if not os.path.exists(path):
            return {"valid": False, "error": f"File not found: {path}"}

        ext = Path(path).suffix.lower()
        if ext not in self.SUPPORTED_FORMATS:
            return {"valid": False, "error": f"Unsupported format: {ext}"}

        try:
            size = os.path.getsize(path)
            if size == 0:
                return {"valid": False, "error": "File is empty"}

            # Count samples
            sample_count = self._count_samples(path, ext)
            return {
                "valid": True,
                "format": ext,
                "size_bytes": size,
                "sample_count": sample_count,
            }
        except Exception as e:
            return {"valid": False, "error": str(e)}

    def _count_samples(self, path: str, ext: str) -> int:
        if ext == ".jsonl":
            with open(path, "r") as f:
                return sum(1 for line in f if line.strip())
        elif ext == ".json":
            with open(path, "r") as f:
                data = json.load(f)
                return len(data) if isinstance(data, list) else 1
        elif ext == ".txt":
            with open(path, "r") as f:
                return sum(1 for line in f if line.strip())
        return -1  # Unknown


class FineTunePipeline:
    """On-device fine-tuning pipeline manager.

    Usage::

        pipeline = FineTunePipeline()
        config = FineTuneConfig(model_name="microsoft/phi-2", method=FineTuneMethod.LORA)
        job = await pipeline.start_job(config)
        status = pipeline.get_job(job.job_id)
    """

    def __init__(self, base_dir: str = "~/.windows_ai/fine_tuned"):
        self._base_dir = os.path.expanduser(base_dir)
        self._jobs: Dict[str, FineTuneJob] = {}
        self._callbacks: List[Callable] = []
        self._validator = DatasetValidator()
        self._next_id = 1
        logger.info("FineTunePipeline initialized, base_dir=%s", self._base_dir)

    def create_job(self, config: FineTuneConfig) -> FineTuneJob:
        """Create a new fine-tuning job (does not start it)."""
        job_id = f"ft-{self._next_id:04d}"
        self._next_id += 1
        job = FineTuneJob(job_id=job_id, config=config)
        self._jobs[job_id] = job
        logger.info("Created fine-tune job %s for model %s", job_id, config.model_name)
        return job

    async def start_job(self, config: FineTuneConfig) -> FineTuneJob:
        """Create and start a fine-tuning job."""
        job = self.create_job(config)
        job.status = FineTuneStatus.PREPARING
        job.started_at = time.time()

        # Validate dataset if provided
        if config.dataset_path:
            validation = self._validator.validate(config.dataset_path)
            if not validation.get("valid"):
                job.status = FineTuneStatus.FAILED
                job.error = validation.get("error", "Dataset validation failed")
                return job
            job.metrics["dataset"] = validation

        # Calculate total steps
        sample_count = job.metrics.get("dataset", {}).get("sample_count", 100)
        steps_per_epoch = max(1, sample_count // config.batch_size)
        job.total_steps = steps_per_epoch * config.epochs

        job.status = FineTuneStatus.TRAINING
        logger.info("Started fine-tune job %s (%d total steps)", job.job_id, job.total_steps)
        return job

    def update_progress(self, job_id: str, step: int, loss: float, **kwargs) -> bool:
        """Update job progress (called by training loop)."""
        job = self._jobs.get(job_id)
        if not job:
            return False

        job.current_step = step
        job.train_loss = loss
        job.progress = step / max(job.total_steps, 1)
        job.current_epoch = step // max(job.total_steps // max(job.config.epochs, 1), 1)
        job.metrics.update(kwargs)

        for cb in self._callbacks:
            try:
                cb(job)
            except Exception:
                pass

        return True

    def complete_job(self, job_id: str, eval_loss: Optional[float] = None) -> bool:
        """Mark a job as completed."""
        job = self._jobs.get(job_id)
        if not job:
            return False
        job.status = FineTuneStatus.COMPLETED
        job.progress = 1.0
        job.eval_loss = eval_loss
        job.completed_at = time.time()
        logger.info("Fine-tune job %s completed", job_id)
        return True

    def fail_job(self, job_id: str, error: str) -> bool:
        """Mark a job as failed."""
        job = self._jobs.get(job_id)
        if not job:
            return False
        job.status = FineTuneStatus.FAILED
        job.error = error
        job.completed_at = time.time()
        logger.error("Fine-tune job %s failed: %s", job_id, error)
        return True

    def cancel_job(self, job_id: str) -> bool:
        """Cancel a running job."""
        job = self._jobs.get(job_id)
        if not job or job.status in (FineTuneStatus.COMPLETED, FineTuneStatus.FAILED):
            return False
        job.status = FineTuneStatus.CANCELLED
        job.completed_at = time.time()
        logger.info("Fine-tune job %s cancelled", job_id)
        return True

    def get_job(self, job_id: str) -> Optional[FineTuneJob]:
        return self._jobs.get(job_id)

    def list_jobs(self) -> List[Dict[str, Any]]:
        return [job.to_dict() for job in self._jobs.values()]

    def on_progress(self, callback: Callable) -> None:
        """Register a progress callback."""
        self._callbacks.append(callback)

    def get_supported_models(self) -> List[Dict[str, Any]]:
        """List models that can be fine-tuned locally."""
        return [
            {"name": "microsoft/phi-2", "params": "2.7B", "methods": ["lora", "qlora"]},
            {"name": "microsoft/phi-3-mini", "params": "3.8B", "methods": ["lora", "qlora"]},
            {"name": "TinyLlama/TinyLlama-1.1B", "params": "1.1B", "methods": ["lora", "qlora", "full"]},
            {"name": "mistralai/Mistral-7B-v0.1", "params": "7B", "methods": ["lora", "qlora"]},
            {"name": "meta-llama/Llama-2-7b", "params": "7B", "methods": ["lora", "qlora"]},
            {"name": "THUDM/chatglm3-6b", "params": "6B", "methods": ["lora", "qlora"]},
            {"name": "stabilityai/stablelm-3b-4e1t", "params": "3B", "methods": ["lora", "qlora", "full"]},
        ]

    def get_stats(self) -> Dict[str, Any]:
        """Get pipeline statistics."""
        jobs = list(self._jobs.values())
        return {
            "total_jobs": len(jobs),
            "active": sum(1 for j in jobs if j.status == FineTuneStatus.TRAINING),
            "completed": sum(1 for j in jobs if j.status == FineTuneStatus.COMPLETED),
            "failed": sum(1 for j in jobs if j.status == FineTuneStatus.FAILED),
            "cancelled": sum(1 for j in jobs if j.status == FineTuneStatus.CANCELLED),
        }
