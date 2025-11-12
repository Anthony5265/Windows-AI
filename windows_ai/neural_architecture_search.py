"""
Neural Architecture Search (NAS) System

Automatically designs optimal neural network architectures for specific tasks
using evolutionary algorithms and reinforcement learning.
"""

from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional, Callable
from datetime import datetime
from pathlib import Path
import json
import logging
from enum import Enum

logger = logging.getLogger(__name__)


class LayerType(Enum):
    """Neural network layer types"""
    CONV = "conv"
    POOL = "pool"
    DENSE = "dense"
    DROPOUT = "dropout"
    BATCHNORM = "batchnorm"
    RESIDUAL = "residual"
    ATTENTION = "attention"


class SearchStrategy(Enum):
    """NAS search strategies"""
    RANDOM = "random"
    EVOLUTIONARY = "evolutionary"
    REINFORCEMENT = "reinforcement"
    GRADIENT_BASED = "gradient_based"


@dataclass
class Layer:
    """Neural network layer definition"""
    layer_id: str
    layer_type: LayerType
    parameters: Dict[str, Any]
    input_shape: Optional[tuple] = None
    output_shape: Optional[tuple] = None


@dataclass
class Architecture:
    """Neural network architecture"""
    architecture_id: str
    name: str
    layers: List[Layer]
    task_type: str  # classification, regression, generation
    performance_metrics: Dict[str, float] = field(default_factory=dict)
    training_time: float = 0.0
    model_size: int = 0  # Number of parameters
    created_at: datetime = field(default_factory=datetime.now)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "architecture_id": self.architecture_id,
            "name": self.name,
            "layers": [
                {
                    "layer_id": l.layer_id,
                    "layer_type": l.layer_type.value,
                    "parameters": l.parameters,
                    "input_shape": l.input_shape,
                    "output_shape": l.output_shape
                }
                for l in self.layers
            ],
            "task_type": self.task_type,
            "performance_metrics": self.performance_metrics,
            "training_time": self.training_time,
            "model_size": self.model_size,
            "created_at": self.created_at.isoformat()
        }


@dataclass
class SearchSpace:
    """NAS search space definition"""
    available_layers: List[LayerType]
    max_depth: int
    max_width: int
    parameter_ranges: Dict[str, tuple]  # (min, max) for each parameter


@dataclass
class SearchResult:
    """Result of architecture search"""
    best_architecture: Architecture
    all_candidates: List[Architecture]
    search_time: float
    iterations: int
    convergence_history: List[float]


class NeuralArchitectureSearch:
    """
    Neural Architecture Search System

    Automatically discovers optimal neural network architectures
    """

    def __init__(self, data_dir: Path):
        self.data_dir = Path(data_dir)
        self.data_dir.mkdir(parents=True, exist_ok=True)

        self.architectures: List[Architecture] = []
        self.search_history: List[SearchResult] = []

        # Load saved data
        self._load_state()

        logger.info("Neural Architecture Search system initialized")

    def define_search_space(
        self,
        task_type: str,
        input_shape: tuple,
        output_shape: tuple
    ) -> SearchSpace:
        """Define search space for a specific task"""
        if task_type == "image_classification":
            available_layers = [
                LayerType.CONV,
                LayerType.POOL,
                LayerType.BATCHNORM,
                LayerType.DROPOUT,
                LayerType.DENSE
            ]
            parameter_ranges = {
                "filters": (16, 512),
                "kernel_size": (3, 7),
                "units": (64, 1024),
                "dropout_rate": (0.1, 0.5)
            }
        elif task_type == "nlp":
            available_layers = [
                LayerType.DENSE,
                LayerType.ATTENTION,
                LayerType.DROPOUT,
                LayerType.RESIDUAL
            ]
            parameter_ranges = {
                "units": (128, 2048),
                "heads": (4, 16),
                "dropout_rate": (0.1, 0.3)
            }
        else:
            available_layers = [LayerType.DENSE, LayerType.DROPOUT]
            parameter_ranges = {
                "units": (32, 512),
                "dropout_rate": (0.1, 0.5)
            }

        return SearchSpace(
            available_layers=available_layers,
            max_depth=20,
            max_width=512,
            parameter_ranges=parameter_ranges
        )

    def search(
        self,
        search_space: SearchSpace,
        task_type: str,
        strategy: SearchStrategy = SearchStrategy.EVOLUTIONARY,
        num_iterations: int = 50,
        population_size: int = 20,
        evaluation_fn: Optional[Callable] = None
    ) -> SearchResult:
        """
        Search for optimal architecture

        Args:
            search_space: Defined search space
            task_type: Type of task
            strategy: Search strategy
            num_iterations: Number of search iterations
            population_size: Population size for evolutionary search
            evaluation_fn: Function to evaluate architectures
        """
        import random
        import time

        start_time = time.time()
        candidates = []
        convergence_history = []

        if strategy == SearchStrategy.EVOLUTIONARY:
            # Initialize population
            population = self._generate_random_population(
                search_space, task_type, population_size
            )

            for iteration in range(num_iterations):
                # Evaluate population
                if evaluation_fn:
                    for arch in population:
                        score = evaluation_fn(arch)
                        arch.performance_metrics["accuracy"] = score
                else:
                    # Simulated evaluation
                    for arch in population:
                        arch.performance_metrics["accuracy"] = random.random()

                # Track best
                best = max(population, key=lambda a: a.performance_metrics.get("accuracy", 0))
                convergence_history.append(best.performance_metrics["accuracy"])
                candidates.extend(population)

                # Selection
                population = sorted(
                    population,
                    key=lambda a: a.performance_metrics.get("accuracy", 0),
                    reverse=True
                )[:population_size // 2]

                # Crossover and mutation
                offspring = []
                while len(offspring) < population_size // 2:
                    parent1, parent2 = random.sample(population, 2)
                    child = self._crossover(parent1, parent2, task_type)
                    child = self._mutate(child, search_space)
                    offspring.append(child)

                population.extend(offspring)

        elif strategy == SearchStrategy.RANDOM:
            # Random search
            for _ in range(num_iterations):
                arch = self._generate_random_architecture(search_space, task_type)
                if evaluation_fn:
                    score = evaluation_fn(arch)
                    arch.performance_metrics["accuracy"] = score
                else:
                    arch.performance_metrics["accuracy"] = random.random()
                candidates.append(arch)
                convergence_history.append(
                    max(c.performance_metrics.get("accuracy", 0) for c in candidates)
                )

        search_time = time.time() - start_time
        best_architecture = max(candidates, key=lambda a: a.performance_metrics.get("accuracy", 0))

        result = SearchResult(
            best_architecture=best_architecture,
            all_candidates=candidates,
            search_time=search_time,
            iterations=num_iterations,
            convergence_history=convergence_history
        )

        self.search_history.append(result)
        self.architectures.append(best_architecture)
        self._save_state()

        logger.info(f"Architecture search completed: {best_architecture.name} "
                   f"(accuracy={best_architecture.performance_metrics.get('accuracy', 0):.4f})")

        return result

    def _generate_random_architecture(
        self,
        search_space: SearchSpace,
        task_type: str
    ) -> Architecture:
        """Generate random architecture within search space"""
        import random
        import uuid

        num_layers = random.randint(3, search_space.max_depth)
        layers = []

        for i in range(num_layers):
            layer_type = random.choice(search_space.available_layers)
            params = {}

            if layer_type == LayerType.CONV:
                params = {
                    "filters": random.randint(*search_space.parameter_ranges.get("filters", (16, 256))),
                    "kernel_size": random.choice([3, 5, 7]),
                    "activation": random.choice(["relu", "leaky_relu", "elu"])
                }
            elif layer_type == LayerType.DENSE:
                params = {
                    "units": random.randint(*search_space.parameter_ranges.get("units", (64, 512))),
                    "activation": random.choice(["relu", "tanh", "sigmoid"])
                }
            elif layer_type == LayerType.DROPOUT:
                params = {
                    "rate": random.uniform(*search_space.parameter_ranges.get("dropout_rate", (0.1, 0.5)))
                }

            layers.append(Layer(
                layer_id=f"layer_{i}",
                layer_type=layer_type,
                parameters=params
            ))

        return Architecture(
            architecture_id=str(uuid.uuid4()),
            name=f"arch_{uuid.uuid4().hex[:8]}",
            layers=layers,
            task_type=task_type
        )

    def _generate_random_population(
        self,
        search_space: SearchSpace,
        task_type: str,
        size: int
    ) -> List[Architecture]:
        """Generate random population"""
        return [
            self._generate_random_architecture(search_space, task_type)
            for _ in range(size)
        ]

    def _crossover(
        self,
        parent1: Architecture,
        parent2: Architecture,
        task_type: str
    ) -> Architecture:
        """Crossover two architectures"""
        import random
        import uuid

        # Single-point crossover
        point = min(len(parent1.layers), len(parent2.layers)) // 2
        child_layers = parent1.layers[:point] + parent2.layers[point:]

        return Architecture(
            architecture_id=str(uuid.uuid4()),
            name=f"arch_{uuid.uuid4().hex[:8]}",
            layers=child_layers,
            task_type=task_type
        )

    def _mutate(
        self,
        architecture: Architecture,
        search_space: SearchSpace,
        mutation_rate: float = 0.2
    ) -> Architecture:
        """Mutate architecture"""
        import random

        if random.random() < mutation_rate:
            # Mutate random layer
            if architecture.layers:
                idx = random.randint(0, len(architecture.layers) - 1)
                layer = architecture.layers[idx]

                # Mutate parameters
                if layer.layer_type == LayerType.CONV and "filters" in layer.parameters:
                    layer.parameters["filters"] = random.randint(
                        *search_space.parameter_ranges.get("filters", (16, 256))
                    )
                elif layer.layer_type == LayerType.DENSE and "units" in layer.parameters:
                    layer.parameters["units"] = random.randint(
                        *search_space.parameter_ranges.get("units", (64, 512))
                    )

        return architecture

    def export_architecture(self, architecture_id: str, format: str = "keras") -> str:
        """Export architecture to framework code"""
        arch = next((a for a in self.architectures if a.architecture_id == architecture_id), None)
        if not arch:
            return ""

        if format == "keras":
            code = "from tensorflow import keras\nfrom tensorflow.keras import layers\n\n"
            code += f"# {arch.name}\n"
            code += "model = keras.Sequential([\n"

            for layer in arch.layers:
                if layer.layer_type == LayerType.CONV:
                    code += f"    layers.Conv2D({layer.parameters.get('filters', 32)}, "
                    code += f"{layer.parameters.get('kernel_size', 3)}, "
                    code += f"activation='{layer.parameters.get('activation', 'relu')}'),\n"
                elif layer.layer_type == LayerType.DENSE:
                    code += f"    layers.Dense({layer.parameters.get('units', 64)}, "
                    code += f"activation='{layer.parameters.get('activation', 'relu')}'),\n"
                elif layer.layer_type == LayerType.DROPOUT:
                    code += f"    layers.Dropout({layer.parameters.get('rate', 0.5)}),\n"
                elif layer.layer_type == LayerType.POOL:
                    code += "    layers.MaxPooling2D(2),\n"

            code += "])\n"
            return code

        return ""

    def get_best_architectures(self, task_type: Optional[str] = None, top_k: int = 10) -> List[Architecture]:
        """Get best performing architectures"""
        filtered = self.architectures
        if task_type:
            filtered = [a for a in filtered if a.task_type == task_type]

        return sorted(
            filtered,
            key=lambda a: a.performance_metrics.get("accuracy", 0),
            reverse=True
        )[:top_k]

    def _save_state(self):
        """Save state to disk"""
        try:
            data = {
                "architectures": [a.to_dict() for a in self.architectures[-100:]],  # Keep last 100
                "search_history_count": len(self.search_history)
            }

            with open(self.data_dir / "nas_state.json", "w") as f:
                json.dump(data, f, indent=2, default=str)
        except Exception as e:
            logger.error(f"Failed to save NAS state: {e}")

    def _load_state(self):
        """Load state from disk"""
        try:
            state_file = self.data_dir / "nas_state.json"
            if state_file.exists():
                with open(state_file, "r") as f:
                    data = json.load(f)
                logger.info(f"Loaded {len(data.get('architectures', []))} architectures")
        except Exception as e:
            logger.error(f"Failed to load NAS state: {e}")


# Global instance
_nas_system: Optional[NeuralArchitectureSearch] = None


def get_nas_system() -> Optional[NeuralArchitectureSearch]:
    """Get global NAS system instance"""
    return _nas_system


def initialize_nas_system(data_dir: Path) -> NeuralArchitectureSearch:
    """Initialize NAS system"""
    global _nas_system
    _nas_system = NeuralArchitectureSearch(data_dir)
    return _nas_system
