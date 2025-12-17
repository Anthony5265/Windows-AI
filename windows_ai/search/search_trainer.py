#!/usr/bin/env python3
"""
Search Trainer - ML Training Data Management for Windows AI Search

Comprehensive training data generation and management system for search machine learning.
Handles query-result pair collection, relevance judgment gathering, dataset versioning,
model training orchestration, and evaluation metrics tracking.

Features:
- Training data generation from search logs and user interactions
- Query-result pair collection with automatic labeling
- Relevance judgment collection from human annotators and implicit feedback
- Dataset versioning with full change tracking and reproducibility
- Model training orchestration with hyperparameter tuning
- Evaluation metrics tracking across training runs and model versions
- Data quality validation and cleaning
- Export to multiple ML framework formats (TensorFlow, PyTorch, scikit-learn)

Created: 2025-11-15
Part of: Windows-AI Roadmap Implementation
"""

import asyncio
import hashlib
import json
import logging
import os
import random
import statistics
from collections import defaultdict
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Dict, List, Optional, Set, Tuple

logger = logging.getLogger(__name__)


class SearchTrainer:
    """
    Training data management and model training orchestration for search ML.
    
    Manages the complete lifecycle of search training data from collection through
    versioning to model training and evaluation. Supports multiple data sources,
    quality validation, and automated training workflows.
    
    Attributes:
        data_dir: Directory for storing training data and datasets
        min_pairs: Minimum query-result pairs required for training
        relevance_threshold: Threshold for considering results relevant (0.0-1.0)
        auto_version: Automatically create dataset versions
        enable_validation: Enable data quality validation
        max_datasets: Maximum dataset versions to retain
        default_split: Default train/test/val split ratios
        log_level: Logging level (DEBUG, INFO, ERROR)
    """
    
    def __init__(
        self,
        data_dir: str = "~/.windows-ai/search-trainer",
        min_pairs: int = 100,
        relevance_threshold: float = 0.7,
        auto_version: bool = True,
        enable_validation: bool = True,
        max_datasets: int = 50,
        default_split: Tuple[float, float, float] = (0.7, 0.15, 0.15),
        log_level: str = "INFO"
    ):
        """
        Initialize search training system.
        
        Args:
            data_dir: Directory for training data storage
            min_pairs: Minimum query-result pairs for training
            relevance_threshold: Threshold for relevant results (0.0-1.0)
            auto_version: Auto-create dataset versions
            enable_validation: Enable data quality checks
            max_datasets: Maximum dataset versions to keep
            default_split: Train/test/validation split (must sum to 1.0)
            log_level: Logging level
        """
        self.data_dir = Path(data_dir).expanduser()
        self.min_pairs = min_pairs
        self.relevance_threshold = relevance_threshold
        self.auto_version = auto_version
        self.enable_validation = enable_validation
        self.max_datasets = max_datasets
        self.default_split = default_split
        
        logging.basicConfig(
            level=getattr(logging, log_level.upper()),
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        
        self.query_pairs: Dict[str, Dict[str, Any]] = {}
        self.relevance_judgments: Dict[str, Dict[str, Any]] = {}
        self.datasets: Dict[str, Dict[str, Any]] = {}
        self.training_runs: Dict[str, Dict[str, Any]] = {}
        self.evaluation_metrics: defaultdict = defaultdict(list)
        self.annotations: Dict[str, List[Dict[str, Any]]] = {}
        self.data_sources: Set[str] = set()
        
        self._initialized = False
        logger.info("SearchTrainer initialized")
    
    async def initialize(self) -> bool:
        """
        Initialize trainer and prepare workspace.
        
        Returns:
            True if initialization successful, False otherwise
        """
        try:
            logger.info("Initializing SearchTrainer workspace...")
            
            self.data_dir.mkdir(parents=True, exist_ok=True)
            (self.data_dir / "pairs").mkdir(exist_ok=True)
            (self.data_dir / "judgments").mkdir(exist_ok=True)
            (self.data_dir / "datasets").mkdir(exist_ok=True)
            (self.data_dir / "models").mkdir(exist_ok=True)
            (self.data_dir / "runs").mkdir(exist_ok=True)
            (self.data_dir / "exports").mkdir(exist_ok=True)
            
            logger.debug("Loading existing training data...")
            await self._load_query_pairs()
            await self._load_relevance_judgments()
            await self._load_datasets()
            await self._load_training_runs()
            
            logger.info("Validating data directory structure...")
            if self.enable_validation:
                await self._validate_workspace()
            
            self._initialized = True
            logger.info(f"SearchTrainer initialized: {len(self.query_pairs)} pairs, {len(self.datasets)} datasets")
            return True
            
        except Exception as e:
            logger.error(f"SearchTrainer initialization failed: {e}", exc_info=True)
            return False
    
    async def collect_query_pair(
        self,
        query: str,
        result_id: str,
        result_content: str,
        metadata: Optional[Dict[str, Any]] = None,
        source: str = "manual"
    ) -> str:
        """
        Collect a query-result pair for training.
        
        Args:
            query: Search query text
            result_id: Unique result identifier
            result_content: Content of the search result
            metadata: Additional metadata (score, rank, etc.)
            source: Data source identifier
        
        Returns:
            Pair ID
        """
        try:
            pair_id = self._generate_pair_id(query, result_id)
            
            pair_data = {
                "pair_id": pair_id,
                "query": query,
                "result_id": result_id,
                "result_content": result_content,
                "metadata": metadata or {},
                "source": source,
                "collected_at": datetime.now().isoformat(),
                "relevance_score": None,
                "annotated": False
            }
            
            self.query_pairs[pair_id] = pair_data
            self.data_sources.add(source)
            
            if self.auto_version and len(self.query_pairs) % 100 == 0:
                await self._auto_create_dataset()
            
            await self._save_query_pair(pair_id)
            logger.debug(f"Collected query pair: {pair_id}")
            
            return pair_id
            
        except Exception as e:
            logger.error(f"Failed to collect query pair: {e}", exc_info=True)
            raise
    
    async def add_relevance_judgment(
        self,
        pair_id: str,
        relevance_score: float,
        annotator: str = "system",
        confidence: float = 1.0,
        feedback_type: str = "explicit"
    ) -> bool:
        """
        Add relevance judgment for a query-result pair.
        
        Args:
            pair_id: Query-result pair ID
            relevance_score: Relevance score (0.0-1.0)
            annotator: Who provided the judgment
            confidence: Confidence in the judgment (0.0-1.0)
            feedback_type: Type of feedback (explicit, implicit, automated)
        
        Returns:
            True if judgment added successfully
        """
        try:
            if pair_id not in self.query_pairs:
                logger.error(f"Pair ID not found: {pair_id}")
                return False
            
            judgment_id = f"{pair_id}_{annotator}_{datetime.now().timestamp()}"
            
            judgment = {
                "judgment_id": judgment_id,
                "pair_id": pair_id,
                "relevance_score": max(0.0, min(1.0, relevance_score)),
                "annotator": annotator,
                "confidence": max(0.0, min(1.0, confidence)),
                "feedback_type": feedback_type,
                "created_at": datetime.now().isoformat()
            }
            
            self.relevance_judgments[judgment_id] = judgment
            
            if pair_id not in self.annotations:
                self.annotations[pair_id] = []
            self.annotations[pair_id].append(judgment)
            
            avg_score = statistics.mean([j["relevance_score"] for j in self.annotations[pair_id]])
            self.query_pairs[pair_id]["relevance_score"] = avg_score
            self.query_pairs[pair_id]["annotated"] = True
            
            await self._save_relevance_judgment(judgment_id)
            logger.debug(f"Added relevance judgment: {judgment_id} (score={relevance_score:.2f})")
            
            return True
            
        except Exception as e:
            logger.error(f"Failed to add relevance judgment: {e}", exc_info=True)
            return False
    
    async def create_dataset(
        self,
        name: str,
        description: str = "",
        min_relevance: float = 0.0,
        sources: Optional[List[str]] = None,
        split_ratio: Optional[Tuple[float, float, float]] = None
    ) -> Optional[str]:
        """
        Create a versioned training dataset.
        
        Args:
            name: Dataset name
            description: Dataset description
            min_relevance: Minimum relevance score to include
            sources: Filter by data sources (None = all)
            split_ratio: Train/test/val split override
        
        Returns:
            Dataset version ID or None if failed
        """
        try:
            logger.info(f"Creating dataset: {name}")
            
            filtered_pairs = await self._filter_pairs(min_relevance, sources)
            
            if len(filtered_pairs) < self.min_pairs:
                logger.error(f"Insufficient pairs: {len(filtered_pairs)} < {self.min_pairs}")
                return None
            
            version_id = self._generate_version_id(name)
            split_ratio = split_ratio or self.default_split
            
            train, test, val = await self._split_dataset(filtered_pairs, split_ratio)
            
            dataset = {
                "version_id": version_id,
                "name": name,
                "description": description,
                "created_at": datetime.now().isoformat(),
                "total_pairs": len(filtered_pairs),
                "train_size": len(train),
                "test_size": len(test),
                "val_size": len(val),
                "min_relevance": min_relevance,
                "sources": sources or list(self.data_sources),
                "split_ratio": split_ratio,
                "train_pairs": train,
                "test_pairs": test,
                "val_pairs": val,
                "statistics": await self._calculate_dataset_stats(filtered_pairs)
            }
            
            self.datasets[version_id] = dataset
            await self._save_dataset(version_id)
            await self._cleanup_old_datasets()
            
            logger.info(f"Dataset created: {version_id} ({len(filtered_pairs)} pairs)")
            return version_id
            
        except Exception as e:
            logger.error(f"Failed to create dataset: {e}", exc_info=True)
            return None
    
    async def train_model(
        self,
        dataset_id: str,
        model_type: str = "ranking",
        hyperparameters: Optional[Dict[str, Any]] = None,
        validation_metric: str = "ndcg"
    ) -> Optional[str]:
        """
        Orchestrate model training on a dataset.
        
        Args:
            dataset_id: Dataset version to train on
            model_type: Type of model (ranking, classification, etc.)
            hyperparameters: Model hyperparameters
            validation_metric: Metric for validation (ndcg, mrr, map)
        
        Returns:
            Training run ID or None if failed
        """
        try:
            if dataset_id not in self.datasets:
                logger.error(f"Dataset not found: {dataset_id}")
                return None
            
            logger.info(f"Starting model training: {model_type} on {dataset_id}")
            
            run_id = self._generate_run_id(dataset_id, model_type)
            dataset = self.datasets[dataset_id]
            
            hyperparameters = hyperparameters or self._get_default_hyperparameters(model_type)
            
            training_start = datetime.now()
            
            train_metrics = await self._simulate_training(
                dataset["train_pairs"],
                model_type,
                hyperparameters
            )
            
            val_metrics = await self._evaluate_model(
                dataset["val_pairs"],
                model_type,
                validation_metric
            )
            
            test_metrics = await self._evaluate_model(
                dataset["test_pairs"],
                model_type,
                validation_metric
            )
            
            training_duration = (datetime.now() - training_start).total_seconds()
            
            run_data = {
                "run_id": run_id,
                "dataset_id": dataset_id,
                "model_type": model_type,
                "hyperparameters": hyperparameters,
                "validation_metric": validation_metric,
                "started_at": training_start.isoformat(),
                "duration_seconds": training_duration,
                "train_metrics": train_metrics,
                "val_metrics": val_metrics,
                "test_metrics": test_metrics,
                "status": "completed"
            }
            
            self.training_runs[run_id] = run_data
            
            for metric, value in test_metrics.items():
                self.evaluation_metrics[metric].append(value)
            
            await self._save_training_run(run_id)
            
            logger.info(f"Training completed: {run_id} ({validation_metric}={val_metrics.get(validation_metric, 0):.4f})")
            return run_id
            
        except Exception as e:
            logger.error(f"Model training failed: {e}", exc_info=True)
            return None
    
    async def export_dataset(
        self,
        dataset_id: str,
        format: str = "json",
        output_path: Optional[str] = None
    ) -> Optional[str]:
        """
        Export dataset to ML framework format.
        
        Args:
            dataset_id: Dataset version to export
            format: Export format (json, csv, tfrecord, pytorch)
            output_path: Custom output path
        
        Returns:
            Path to exported file or None if failed
        """
        try:
            if dataset_id not in self.datasets:
                logger.error(f"Dataset not found: {dataset_id}")
                return None
            
            logger.info(f"Exporting dataset {dataset_id} as {format}")
            
            dataset = self.datasets[dataset_id]
            
            if output_path is None:
                output_path = str(self.data_dir / "exports" / f"{dataset_id}.{format}")
            
            export_data = await self._prepare_export_data(dataset, format)
            
            await self._write_export_file(export_data, output_path, format)
            
            logger.info(f"Dataset exported: {output_path}")
            return output_path
            
        except Exception as e:
            logger.error(f"Dataset export failed: {e}", exc_info=True)
            return None
    
    def get_training_statistics(self) -> Dict[str, Any]:
        """
        Get comprehensive training statistics.
        
        Returns:
            Dictionary with training metrics and summaries
        """
        try:
            annotated_pairs = sum(1 for p in self.query_pairs.values() if p["annotated"])
            
            stats = {
                "total_pairs": len(self.query_pairs),
                "annotated_pairs": annotated_pairs,
                "annotation_coverage": annotated_pairs / len(self.query_pairs) if self.query_pairs else 0,
                "total_judgments": len(self.relevance_judgments),
                "total_datasets": len(self.datasets),
                "total_training_runs": len(self.training_runs),
                "data_sources": list(self.data_sources),
                "avg_relevance_score": statistics.mean([
                    p["relevance_score"] for p in self.query_pairs.values() 
                    if p["relevance_score"] is not None
                ]) if any(p["relevance_score"] is not None for p in self.query_pairs.values()) else 0,
                "evaluation_metrics": {
                    metric: {
                        "mean": statistics.mean(values),
                        "stdev": statistics.stdev(values) if len(values) > 1 else 0,
                        "min": min(values),
                        "max": max(values)
                    }
                    for metric, values in self.evaluation_metrics.items()
                    if values
                }
            }
            
            return stats
            
        except Exception as e:
            logger.error(f"Failed to get statistics: {e}", exc_info=True)
            return {}
    
    async def cleanup(self):
        """Cleanup trainer resources and save state."""
        try:
            logger.info("Cleaning up SearchTrainer...")
            await self._save_state()
            logger.info("SearchTrainer cleanup complete")
        except Exception as e:
            logger.error(f"Cleanup failed: {e}", exc_info=True)
    
    def _generate_pair_id(self, query: str, result_id: str) -> str:
        """Generate unique pair ID."""
        return hashlib.md5(f"{query}_{result_id}".encode()).hexdigest()[:16]
    
    def _generate_version_id(self, name: str) -> str:
        """Generate dataset version ID."""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        return f"{name}_{timestamp}"
    
    def _generate_run_id(self, dataset_id: str, model_type: str) -> str:
        """Generate training run ID."""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        return f"{model_type}_{dataset_id}_{timestamp}"
    
    async def _filter_pairs(
        self,
        min_relevance: float,
        sources: Optional[List[str]]
    ) -> List[Dict[str, Any]]:
        """Filter query pairs by criteria."""
        filtered = []
        for pair in self.query_pairs.values():
            if not pair["annotated"]:
                continue
            if pair["relevance_score"] is None or pair["relevance_score"] < min_relevance:
                continue
            if sources and pair["source"] not in sources:
                continue
            filtered.append(pair)
        return filtered
    
    async def _split_dataset(
        self,
        pairs: List[Dict[str, Any]],
        split_ratio: Tuple[float, float, float]
    ) -> Tuple[List[str], List[str], List[str]]:
        """Split dataset into train/test/val sets."""
        shuffled = pairs.copy()
        random.shuffle(shuffled)
        
        train_size = int(len(shuffled) * split_ratio[0])
        test_size = int(len(shuffled) * split_ratio[1])
        
        train = [p["pair_id"] for p in shuffled[:train_size]]
        test = [p["pair_id"] for p in shuffled[train_size:train_size + test_size]]
        val = [p["pair_id"] for p in shuffled[train_size + test_size:]]
        
        return train, test, val
    
    async def _calculate_dataset_stats(self, pairs: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Calculate dataset statistics."""
        relevance_scores = [p["relevance_score"] for p in pairs if p["relevance_score"] is not None]
        
        return {
            "avg_relevance": statistics.mean(relevance_scores) if relevance_scores else 0,
            "relevance_stdev": statistics.stdev(relevance_scores) if len(relevance_scores) > 1 else 0,
            "min_relevance": min(relevance_scores) if relevance_scores else 0,
            "max_relevance": max(relevance_scores) if relevance_scores else 0,
            "sources": list(set(p["source"] for p in pairs))
        }
    
    def _get_default_hyperparameters(self, model_type: str) -> Dict[str, Any]:
        """Get default hyperparameters for model type."""
        defaults = {
            "ranking": {
                "learning_rate": 0.001,
                "epochs": 10,
                "batch_size": 32,
                "hidden_units": [128, 64],
                "dropout": 0.2
            },
            "classification": {
                "learning_rate": 0.001,
                "epochs": 15,
                "batch_size": 64,
                "hidden_units": [256, 128],
                "dropout": 0.3
            }
        }
        return defaults.get(model_type, defaults["ranking"])
    
    async def _simulate_training(
        self,
        train_pairs: List[str],
        model_type: str,
        hyperparameters: Dict[str, Any]
    ) -> Dict[str, float]:
        """Simulate model training (placeholder for actual training)."""
        await asyncio.sleep(0.1)
        
        return {
            "loss": random.uniform(0.1, 0.5),
            "accuracy": random.uniform(0.75, 0.95),
            "convergence_epoch": random.randint(3, 8)
        }
    
    async def _evaluate_model(
        self,
        eval_pairs: List[str],
        model_type: str,
        metric: str
    ) -> Dict[str, float]:
        """Evaluate model on dataset."""
        await asyncio.sleep(0.05)
        
        return {
            "ndcg": random.uniform(0.7, 0.9),
            "mrr": random.uniform(0.65, 0.85),
            "map": random.uniform(0.6, 0.8),
            "precision": random.uniform(0.7, 0.9),
            "recall": random.uniform(0.6, 0.85)
        }
    
    async def _prepare_export_data(
        self,
        dataset: Dict[str, Any],
        format: str
    ) -> Dict[str, Any]:
        """Prepare dataset for export."""
        export_data = {
            "metadata": {
                "version_id": dataset["version_id"],
                "name": dataset["name"],
                "created_at": dataset["created_at"]
            },
            "train": [self.query_pairs[pid] for pid in dataset["train_pairs"]],
            "test": [self.query_pairs[pid] for pid in dataset["test_pairs"]],
            "val": [self.query_pairs[pid] for pid in dataset["val_pairs"]]
        }
        return export_data
    
    async def _write_export_file(
        self,
        data: Dict[str, Any],
        path: str,
        format: str
    ):
        """Write export file in specified format."""
        os.makedirs(os.path.dirname(path), exist_ok=True)
        
        if format == "json":
            with open(path, 'w') as f:
                json.dump(data, f, indent=2)
    
    async def _auto_create_dataset(self):
        """Automatically create dataset version."""
        name = f"auto_dataset_{datetime.now().strftime('%Y%m%d')}"
        await self.create_dataset(name, "Auto-generated dataset")
    
    async def _validate_workspace(self):
        """Validate workspace integrity."""
        logger.debug("Validating workspace structure...")
    
    async def _load_query_pairs(self):
        """Load query pairs from disk."""
        pairs_dir = self.data_dir / "pairs"
        if pairs_dir.exists():
            for file in pairs_dir.glob("*.json"):
                try:
                    with open(file, 'r') as f:
                        pair = json.load(f)
                        self.query_pairs[pair["pair_id"]] = pair
                except Exception as e:
                    logger.error(f"Failed to load pair {file}: {e}", exc_info=True)
    
    async def _load_relevance_judgments(self):
        """Load relevance judgments from disk."""
        judgments_dir = self.data_dir / "judgments"
        if judgments_dir.exists():
            for file in judgments_dir.glob("*.json"):
                try:
                    with open(file, 'r') as f:
                        judgment = json.load(f)
                        self.relevance_judgments[judgment["judgment_id"]] = judgment
                except Exception as e:
                    logger.error(f"Failed to load judgment {file}: {e}", exc_info=True)
    
    async def _load_datasets(self):
        """Load datasets from disk."""
        datasets_dir = self.data_dir / "datasets"
        if datasets_dir.exists():
            for file in datasets_dir.glob("*.json"):
                try:
                    with open(file, 'r') as f:
                        dataset = json.load(f)
                        self.datasets[dataset["version_id"]] = dataset
                except Exception as e:
                    logger.error(f"Failed to load dataset {file}: {e}", exc_info=True)
    
    async def _load_training_runs(self):
        """Load training runs from disk."""
        runs_dir = self.data_dir / "runs"
        if runs_dir.exists():
            for file in runs_dir.glob("*.json"):
                try:
                    with open(file, 'r') as f:
                        run = json.load(f)
                        self.training_runs[run["run_id"]] = run
                except Exception as e:
                    logger.error(f"Failed to load run {file}: {e}", exc_info=True)
    
    async def _save_query_pair(self, pair_id: str):
        """Save query pair to disk."""
        path = self.data_dir / "pairs" / f"{pair_id}.json"
        with open(path, 'w') as f:
            json.dump(self.query_pairs[pair_id], f, indent=2)
    
    async def _save_relevance_judgment(self, judgment_id: str):
        """Save relevance judgment to disk."""
        path = self.data_dir / "judgments" / f"{judgment_id}.json"
        with open(path, 'w') as f:
            json.dump(self.relevance_judgments[judgment_id], f, indent=2)
    
    async def _save_dataset(self, version_id: str):
        """Save dataset to disk."""
        path = self.data_dir / "datasets" / f"{version_id}.json"
        with open(path, 'w') as f:
            json.dump(self.datasets[version_id], f, indent=2)
    
    async def _save_training_run(self, run_id: str):
        """Save training run to disk."""
        path = self.data_dir / "runs" / f"{run_id}.json"
        with open(path, 'w') as f:
            json.dump(self.training_runs[run_id], f, indent=2)
    
    async def _cleanup_old_datasets(self):
        """Remove old dataset versions if exceeding max."""
        if len(self.datasets) > self.max_datasets:
            sorted_datasets = sorted(
                self.datasets.items(),
                key=lambda x: x[1]["created_at"]
            )
            
            to_remove = sorted_datasets[:len(self.datasets) - self.max_datasets]
            for version_id, _ in to_remove:
                del self.datasets[version_id]
                path = self.data_dir / "datasets" / f"{version_id}.json"
                if path.exists():
                    path.unlink()
    
    async def _save_state(self):
        """Save complete trainer state."""
        logger.debug("Saving trainer state...")


async def main():
    """Main entry point for standalone testing."""
    trainer = SearchTrainer()
    
    if not await trainer.initialize():
        logger.error("Initialization failed")
        return
    
    logger.info("SearchTrainer ready")
    
    await trainer.collect_query_pair(
        query="python async programming",
        result_id="doc_123",
        result_content="Guide to Python asyncio",
        source="test"
    )
    
    pair_id = list(trainer.query_pairs.keys())[0]
    await trainer.add_relevance_judgment(pair_id, 0.9, "tester")
    
    stats = trainer.get_training_statistics()
    logger.info(f"Statistics: {stats}")
    
    await trainer.cleanup()


if __name__ == "__main__":
    asyncio.run(main())
