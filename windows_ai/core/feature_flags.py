"""
Feature Flags — Dynamic feature flag management with targeting rules,
gradual rollout, A/B testing integration, and audit logging.
"""
import logging
import time
import uuid
import hashlib
from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional, Set
from enum import Enum

logger = logging.getLogger(__name__)


class FlagStatus(Enum):
    ENABLED = "enabled"
    DISABLED = "disabled"
    PERCENTAGE = "percentage"
    TARGETED = "targeted"


class RolloutStrategy(Enum):
    ALL = "all"
    PERCENTAGE = "percentage"
    USER_LIST = "user_list"
    ATTRIBUTE = "attribute"
    GRADUAL = "gradual"


@dataclass
class TargetingRule:
    rule_id: str
    attribute: str
    operator: str  # eq, neq, contains, gt, lt, in, not_in, regex
    value: Any
    negate: bool = False

    def evaluate(self, context: Dict[str, Any]) -> bool:
        actual = context.get(self.attribute)
        if actual is None:
            result = False
        elif self.operator == "eq":
            result = actual == self.value
        elif self.operator == "neq":
            result = actual != self.value
        elif self.operator == "contains":
            result = str(self.value) in str(actual)
        elif self.operator == "gt":
            result = float(actual) > float(self.value)
        elif self.operator == "lt":
            result = float(actual) < float(self.value)
        elif self.operator == "in":
            result = actual in self.value
        elif self.operator == "not_in":
            result = actual not in self.value
        elif self.operator == "regex":
            import re
            result = bool(re.search(str(self.value), str(actual)))
        else:
            result = False
        return not result if self.negate else result


@dataclass
class FeatureFlag:
    flag_id: str
    key: str
    name: str
    description: str = ""
    status: FlagStatus = FlagStatus.DISABLED
    percentage: float = 0.0
    targeting_rules: List[TargetingRule] = field(default_factory=list)
    allowed_users: Set[str] = field(default_factory=set)
    blocked_users: Set[str] = field(default_factory=set)
    default_value: Any = False
    variants: Dict[str, Any] = field(default_factory=dict)
    created_at: float = field(default_factory=time.time)
    updated_at: float = field(default_factory=time.time)
    tags: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)
    rollout_start: Optional[float] = None
    rollout_end: Optional[float] = None
    rollout_strategy: RolloutStrategy = RolloutStrategy.ALL

    def evaluate(self, user_id: str = "", context: Dict[str, Any] = None) -> Any:
        context = context or {}
        # Check blocked users first
        if user_id in self.blocked_users:
            return self.default_value
        # Check allowed users
        if user_id in self.allowed_users:
            return True if not self.variants else list(self.variants.values())[0]

        if self.status == FlagStatus.DISABLED:
            return self.default_value
        elif self.status == FlagStatus.ENABLED:
            return True if not self.variants else list(self.variants.values())[0]
        elif self.status == FlagStatus.PERCENTAGE:
            return self._check_percentage(user_id)
        elif self.status == FlagStatus.TARGETED:
            return self._check_targeting(context)
        return self.default_value

    def _check_percentage(self, user_id: str) -> bool:
        if not user_id:
            return False
        hash_val = int(hashlib.md5(f"{self.key}:{user_id}".encode()).hexdigest(), 16)
        bucket = (hash_val % 10000) / 100.0
        if self.rollout_strategy == RolloutStrategy.GRADUAL and self.rollout_start and self.rollout_end:
            now = time.time()
            if now < self.rollout_start:
                return False
            if now > self.rollout_end:
                return bucket < self.percentage
            progress = (now - self.rollout_start) / (self.rollout_end - self.rollout_start)
            current_pct = self.percentage * progress
            return bucket < current_pct
        return bucket < self.percentage

    def _check_targeting(self, context: Dict[str, Any]) -> bool:
        if not self.targeting_rules:
            return self.status == FlagStatus.ENABLED
        return all(rule.evaluate(context) for rule in self.targeting_rules)


@dataclass
class FlagEvaluation:
    flag_key: str
    user_id: str
    value: Any
    reason: str
    timestamp: float = field(default_factory=time.time)


class FeatureFlagManager:
    """Manages feature flags with evaluation, audit, and analytics."""

    def __init__(self):
        self._flags: Dict[str, FeatureFlag] = {}
        self._evaluations: List[FlagEvaluation] = []
        self._overrides: Dict[str, Dict[str, Any]] = {}  # flag_key -> {user_id: value}
        logger.info("FeatureFlagManager initialized")

    def create_flag(self, key: str, name: str, description: str = "",
                    default_value: Any = False, tags: List[str] = None) -> FeatureFlag:
        flag = FeatureFlag(
            flag_id=str(uuid.uuid4()), key=key, name=name,
            description=description, default_value=default_value, tags=tags or []
        )
        self._flags[key] = flag
        logger.info(f"Feature flag created: {key}")
        return flag

    def enable(self, key: str) -> bool:
        flag = self._flags.get(key)
        if not flag:
            return False
        flag.status = FlagStatus.ENABLED
        flag.updated_at = time.time()
        return True

    def disable(self, key: str) -> bool:
        flag = self._flags.get(key)
        if not flag:
            return False
        flag.status = FlagStatus.DISABLED
        flag.updated_at = time.time()
        return True

    def set_percentage(self, key: str, percentage: float) -> bool:
        flag = self._flags.get(key)
        if not flag:
            return False
        flag.status = FlagStatus.PERCENTAGE
        flag.percentage = max(0, min(100, percentage))
        flag.updated_at = time.time()
        return True

    def set_gradual_rollout(self, key: str, target_percentage: float,
                            duration_hours: float = 24) -> bool:
        flag = self._flags.get(key)
        if not flag:
            return False
        flag.status = FlagStatus.PERCENTAGE
        flag.percentage = target_percentage
        flag.rollout_strategy = RolloutStrategy.GRADUAL
        flag.rollout_start = time.time()
        flag.rollout_end = time.time() + duration_hours * 3600
        flag.updated_at = time.time()
        return True

    def add_targeting_rule(self, key: str, attribute: str, operator: str, value: Any) -> bool:
        flag = self._flags.get(key)
        if not flag:
            return False
        rule = TargetingRule(str(uuid.uuid4()), attribute, operator, value)
        flag.targeting_rules.append(rule)
        flag.status = FlagStatus.TARGETED
        flag.updated_at = time.time()
        return True

    def set_override(self, key: str, user_id: str, value: Any):
        self._overrides.setdefault(key, {})[user_id] = value

    def evaluate(self, key: str, user_id: str = "", context: Dict[str, Any] = None) -> Any:
        # Check overrides first
        override = self._overrides.get(key, {}).get(user_id)
        if override is not None:
            self._log_evaluation(key, user_id, override, "override")
            return override

        flag = self._flags.get(key)
        if not flag:
            return False

        value = flag.evaluate(user_id, context)
        reason = f"status:{flag.status.value}"
        self._log_evaluation(key, user_id, value, reason)
        return value

    def is_enabled(self, key: str, user_id: str = "", context: Dict[str, Any] = None) -> bool:
        return bool(self.evaluate(key, user_id, context))

    def _log_evaluation(self, key: str, user_id: str, value: Any, reason: str):
        ev = FlagEvaluation(key, user_id, value, reason)
        self._evaluations.append(ev)
        if len(self._evaluations) > 100000:
            self._evaluations = self._evaluations[-50000:]

    def get_flag(self, key: str) -> Optional[FeatureFlag]:
        return self._flags.get(key)

    def list_flags(self, tag: str = None) -> List[Dict[str, Any]]:
        flags = self._flags.values()
        if tag:
            flags = [f for f in flags if tag in f.tags]
        return [
            {"key": f.key, "name": f.name, "status": f.status.value,
             "percentage": f.percentage, "tags": f.tags}
            for f in flags
        ]

    def get_analytics(self, key: str) -> Dict[str, Any]:
        evals = [e for e in self._evaluations if e.flag_key == key]
        total = len(evals)
        enabled = sum(1 for e in evals if e.value)
        return {
            "total_evaluations": total,
            "enabled_count": enabled,
            "disabled_count": total - enabled,
            "enabled_rate": enabled / total if total > 0 else 0,
        }

    def delete_flag(self, key: str) -> bool:
        if key in self._flags:
            del self._flags[key]
            return True
        return False


# Global instance
_manager: Optional[FeatureFlagManager] = None

def get_feature_flags() -> FeatureFlagManager:
    global _manager
    if _manager is None:
        _manager = FeatureFlagManager()
    return _manager
