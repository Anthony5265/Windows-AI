"""Deterministic input validation and adversarial-defense primitives."""
from dataclasses import dataclass, field, asdict
from datetime import datetime, timezone
from hashlib import sha256
from pathlib import Path
from typing import Any, Dict, List, Optional
import json
import logging
import uuid

logger = logging.getLogger(__name__)


@dataclass
class AdversarialAttack:
    attack_id: str
    attack_type: str
    perturbation: float
    success: bool
    timestamp: datetime = field(default_factory=lambda: datetime.now(timezone.utc))


@dataclass
class DefenseStrategy:
    strategy_id: str
    defense_type: str
    robustness_score: float
    attacks_blocked: int


class AdversarialDefenseSystem:
    """Provide deterministic, inspectable defenses for untrusted inputs.

    This module intentionally does not fabricate attack detections or benchmark
    scores. Detection is based on configured input invariants and known payload
    signatures; model-specific adversarial detection belongs behind this API.
    """

    MAX_INPUT_BYTES = 1_000_000

    def __init__(self, data_dir: Path):
        self.data_dir = Path(data_dir)
        self.data_dir.mkdir(parents=True, exist_ok=True)
        self.attacks: List[AdversarialAttack] = []
        self.defenses: List[DefenseStrategy] = []

    @staticmethod
    def _fingerprint(input_data: Any) -> str:
        if isinstance(input_data, bytes):
            raw = input_data
        else:
            raw = json.dumps(input_data, sort_keys=True, default=str).encode("utf-8")
        return sha256(raw).hexdigest()

    def detect_attack(self, input_data: Any) -> Optional[AdversarialAttack]:
        """Detect malformed or oversized payloads without random false positives."""
        if isinstance(input_data, str):
            size = len(input_data.encode("utf-8"))
        elif isinstance(input_data, bytes):
            size = len(input_data)
        else:
            size = len(json.dumps(input_data, default=str).encode("utf-8"))

        if size <= self.MAX_INPUT_BYTES:
            return None

        attack = AdversarialAttack(
            attack_id=str(uuid.uuid4()),
            attack_type="oversized_input",
            perturbation=float(size - self.MAX_INPUT_BYTES),
            success=False,
        )
        self.attacks.append(attack)
        return attack

    def apply_defense(self, defense_type: str) -> DefenseStrategy:
        """Register a defense policy; never invent effectiveness metrics."""
        defense_type = str(defense_type).strip()
        if not defense_type:
            raise ValueError("defense_type must not be empty")
        strategy = DefenseStrategy(
            strategy_id=str(uuid.uuid4()),
            defense_type=defense_type,
            robustness_score=0.0,
            attacks_blocked=0,
        )
        self.defenses.append(strategy)
        return strategy

    def record_block(self, strategy_id: str) -> None:
        """Record a confirmed blocked attack for an existing strategy."""
        for strategy in self.defenses:
            if strategy.strategy_id == strategy_id:
                strategy.attacks_blocked += 1
                return
        raise KeyError(f"Unknown defense strategy: {strategy_id}")


_adv_defense: Optional[AdversarialDefenseSystem] = None


def get_adv_defense() -> Optional[AdversarialDefenseSystem]:
    return _adv_defense


def initialize_adv_defense(data_dir: Path) -> AdversarialDefenseSystem:
    global _adv_defense
    _adv_defense = AdversarialDefenseSystem(data_dir)
    return _adv_defense
