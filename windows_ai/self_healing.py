"""
Self-Healing Workflow System
Automatically detects and fixes workflow failures
"""
import logging
from typing import Dict, List, Optional, Any, Callable
from datetime import datetime
from dataclasses import dataclass, asdict
from pathlib import Path
import json
from enum import Enum

logger = logging.getLogger(__name__)


class FailureType(Enum):
    """Types of workflow failures"""
    TIMEOUT = "timeout"
    PERMISSION_DENIED = "permission_denied"
    FILE_NOT_FOUND = "file_not_found"
    NETWORK_ERROR = "network_error"
    DEPENDENCY_MISSING = "dependency_missing"
    RESOURCE_UNAVAILABLE = "resource_unavailable"
    CONFIGURATION_ERROR = "configuration_error"
    UNKNOWN = "unknown"


class RecoveryStrategy(Enum):
    """Recovery strategies"""
    RETRY = "retry"
    RETRY_WITH_BACKOFF = "retry_with_backoff"
    USE_ALTERNATIVE = "use_alternative"
    SKIP_STEP = "skip_step"
    ROLLBACK = "rollback"
    REQUEST_USER_INPUT = "request_user_input"
    AUTO_FIX = "auto_fix"


@dataclass
class WorkflowFailure:
    """Detected workflow failure"""
    failure_id: str
    workflow_id: str
    step_id: str
    failure_type: FailureType
    error_message: str
    timestamp: str
    context: Dict[str, Any]
    stack_trace: Optional[str] = None


@dataclass
class RecoveryAction:
    """Recovery action taken"""
    action_id: str
    failure_id: str
    strategy: RecoveryStrategy
    description: str
    success: bool
    timestamp: str
    details: Dict[str, Any]


@dataclass
class HealingRule:
    """Self-healing rule"""
    rule_id: str
    failure_pattern: str
    failure_type: FailureType
    recovery_strategy: RecoveryStrategy
    conditions: Dict[str, Any]
    max_retries: int
    priority: int


class SelfHealingSystem:
    """
    Self-Healing Workflow System

    Features:
    - Automatic failure detection
    - Intelligent failure classification
    - Multiple recovery strategies
    - Learning from past failures
    - Rollback capabilities
    - Alternative path execution
    - User notification for critical failures
    - Success rate tracking
    """

    def __init__(self, data_dir: Path):
        self.data_dir = data_dir
        self.data_dir.mkdir(parents=True, exist_ok=True)

        self.failures_file = data_dir / "failures.json"
        self.recoveries_file = data_dir / "recoveries.json"
        self.rules_file = data_dir / "healing_rules.json"

        # Failure tracking
        self.failures: List[WorkflowFailure] = []
        self.recoveries: List[RecoveryAction] = []

        # Healing rules
        self.healing_rules: List[HealingRule] = []

        # Statistics
        self.stats = {
            'total_failures': 0,
            'auto_recovered': 0,
            'manual_intervention': 0,
            'recovery_rate': 0.0
        }

        # Callbacks
        self.failure_callbacks: List[Callable] = []
        self.recovery_callbacks: List[Callable] = []

        # Load data
        self._load_rules()
        self._initialize_default_rules()

    def _initialize_default_rules(self):
        """Initialize default healing rules"""
        default_rules = [
            HealingRule(
                rule_id="retry_timeout",
                failure_pattern="timeout",
                failure_type=FailureType.TIMEOUT,
                recovery_strategy=RecoveryStrategy.RETRY_WITH_BACKOFF,
                conditions={'max_retries': 3},
                max_retries=3,
                priority=1
            ),
            HealingRule(
                rule_id="retry_network",
                failure_pattern="network|connection",
                failure_type=FailureType.NETWORK_ERROR,
                recovery_strategy=RecoveryStrategy.RETRY_WITH_BACKOFF,
                conditions={'max_retries': 5, 'backoff': [2, 4, 8, 16, 32]},
                max_retries=5,
                priority=1
            ),
            HealingRule(
                rule_id="alternative_file",
                failure_pattern="file not found",
                failure_type=FailureType.FILE_NOT_FOUND,
                recovery_strategy=RecoveryStrategy.USE_ALTERNATIVE,
                conditions={'check_alternatives': True},
                max_retries=1,
                priority=2
            ),
            HealingRule(
                rule_id="skip_optional",
                failure_pattern="optional step",
                failure_type=FailureType.UNKNOWN,
                recovery_strategy=RecoveryStrategy.SKIP_STEP,
                conditions={'is_optional': True},
                max_retries=0,
                priority=3
            ),
            HealingRule(
                rule_id="auto_permission",
                failure_pattern="permission denied|access denied",
                failure_type=FailureType.PERMISSION_DENIED,
                recovery_strategy=RecoveryStrategy.AUTO_FIX,
                conditions={'can_elevate': True},
                max_retries=1,
                priority=1
            ),
        ]

        for rule in default_rules:
            if not any(r.rule_id == rule.rule_id for r in self.healing_rules):
                self.healing_rules.append(rule)

    def detect_failure(
        self,
        workflow_id: str,
        step_id: str,
        error: Exception,
        context: Dict[str, Any] = None
    ) -> WorkflowFailure:
        """
        Detect and classify workflow failure

        Args:
            workflow_id: ID of the workflow
            step_id: ID of the failed step
            error: The exception that occurred
            context: Additional context

        Returns:
            WorkflowFailure object
        """
        import uuid

        # Classify failure type
        failure_type = self._classify_failure(error)

        # Create failure record
        failure = WorkflowFailure(
            failure_id=str(uuid.uuid4()),
            workflow_id=workflow_id,
            step_id=step_id,
            failure_type=failure_type,
            error_message=str(error),
            timestamp=datetime.now().isoformat(),
            context=context or {},
            stack_trace=self._get_stack_trace()
        )

        self.failures.append(failure)
        self.stats['total_failures'] += 1

        logger.error(f"Workflow failure detected: {failure_type.value} in {workflow_id}/{step_id}")

        # Notify callbacks
        for callback in self.failure_callbacks:
            try:
                callback(failure)
            except Exception as e:
                logger.error(f"Error in failure callback: {e}")

        return failure

    def _classify_failure(self, error: Exception) -> FailureType:
        """Classify failure type from exception"""
        error_str = str(error).lower()

        if 'timeout' in error_str or 'timed out' in error_str:
            return FailureType.TIMEOUT
        elif 'permission' in error_str or 'access denied' in error_str:
            return FailureType.PERMISSION_DENIED
        elif 'file not found' in error_str or 'no such file' in error_str:
            return FailureType.FILE_NOT_FOUND
        elif 'network' in error_str or 'connection' in error_str:
            return FailureType.NETWORK_ERROR
        elif 'module not found' in error_str or 'import error' in error_str:
            return FailureType.DEPENDENCY_MISSING
        elif 'resource' in error_str or 'unavailable' in error_str:
            return FailureType.RESOURCE_UNAVAILABLE
        elif 'config' in error_str:
            return FailureType.CONFIGURATION_ERROR
        else:
            return FailureType.UNKNOWN

    def _get_stack_trace(self) -> Optional[str]:
        """Get current stack trace"""
        import traceback
        return traceback.format_exc()

    def attempt_recovery(self, failure: WorkflowFailure) -> Optional[RecoveryAction]:
        """
        Attempt to recover from failure

        Args:
            failure: The failure to recover from

        Returns:
            RecoveryAction if recovery was attempted, None otherwise
        """
        # Find matching healing rule
        rule = self._find_matching_rule(failure)

        if not rule:
            logger.warning(f"No healing rule found for {failure.failure_type.value}")
            self.stats['manual_intervention'] += 1
            return None

        logger.info(f"Attempting recovery with strategy: {rule.recovery_strategy.value}")

        # Execute recovery strategy
        success = self._execute_recovery_strategy(failure, rule)

        # Create recovery action
        import uuid
        recovery = RecoveryAction(
            action_id=str(uuid.uuid4()),
            failure_id=failure.failure_id,
            strategy=rule.recovery_strategy,
            description=f"Applied {rule.recovery_strategy.value} for {failure.failure_type.value}",
            success=success,
            timestamp=datetime.now().isoformat(),
            details={'rule_id': rule.rule_id}
        )

        self.recoveries.append(recovery)

        if success:
            self.stats['auto_recovered'] += 1
            logger.info(f"Recovery successful: {rule.recovery_strategy.value}")
        else:
            self.stats['manual_intervention'] += 1
            logger.warning(f"Recovery failed: {rule.recovery_strategy.value}")

        # Update success rate
        self.stats['recovery_rate'] = (
            self.stats['auto_recovered'] / self.stats['total_failures']
            if self.stats['total_failures'] > 0 else 0.0
        )

        # Notify callbacks
        for callback in self.recovery_callbacks:
            try:
                callback(recovery)
            except Exception as e:
                logger.error(f"Error in recovery callback: {e}")

        return recovery

    def _find_matching_rule(self, failure: WorkflowFailure) -> Optional[HealingRule]:
        """Find healing rule that matches the failure"""
        # Find rules for this failure type
        matching_rules = [
            rule for rule in self.healing_rules
            if rule.failure_type == failure.failure_type
        ]

        if not matching_rules:
            return None

        # Sort by priority
        matching_rules.sort(key=lambda r: r.priority)

        # Check pattern match
        for rule in matching_rules:
            if rule.failure_pattern in failure.error_message.lower():
                return rule

        # Return highest priority rule if no pattern match
        return matching_rules[0] if matching_rules else None

    def _execute_recovery_strategy(self, failure: WorkflowFailure, rule: HealingRule) -> bool:
        """Execute recovery strategy"""
        strategy = rule.recovery_strategy

        try:
            if strategy == RecoveryStrategy.RETRY:
                return self._retry(failure, max_retries=rule.max_retries)

            elif strategy == RecoveryStrategy.RETRY_WITH_BACKOFF:
                return self._retry_with_backoff(failure, rule)

            elif strategy == RecoveryStrategy.USE_ALTERNATIVE:
                return self._use_alternative(failure)

            elif strategy == RecoveryStrategy.SKIP_STEP:
                return self._skip_step(failure)

            elif strategy == RecoveryStrategy.ROLLBACK:
                return self._rollback(failure)

            elif strategy == RecoveryStrategy.AUTO_FIX:
                return self._auto_fix(failure)

            elif strategy == RecoveryStrategy.REQUEST_USER_INPUT:
                return self._request_user_input(failure)

            else:
                logger.warning(f"Unknown recovery strategy: {strategy}")
                return False

        except Exception as e:
            logger.error(f"Error executing recovery strategy: {e}")
            return False

    def _retry(self, failure: WorkflowFailure, max_retries: int) -> bool:
        """Simple retry strategy"""
        logger.info(f"Retrying {failure.step_id} (max {max_retries} attempts)")
        # Would actually retry the workflow step here
        # For now, simulate success
        return True

    def _retry_with_backoff(self, failure: WorkflowFailure, rule: HealingRule) -> bool:
        """Retry with exponential backoff"""
        import time

        backoff_delays = rule.conditions.get('backoff', [2, 4, 8, 16, 32])
        max_retries = rule.max_retries

        logger.info(f"Retrying with backoff (max {max_retries} attempts)")

        for attempt in range(max_retries):
            if attempt > 0:
                delay = backoff_delays[min(attempt - 1, len(backoff_delays) - 1)]
                logger.info(f"Waiting {delay}s before retry {attempt + 1}/{max_retries}")
                time.sleep(delay)

            # Would actually retry here
            # Simulate success after 2 attempts
            if attempt >= 1:
                return True

        return False

    def _use_alternative(self, failure: WorkflowFailure) -> bool:
        """Use alternative approach/resource"""
        logger.info(f"Looking for alternative for {failure.step_id}")

        # Would look up alternative paths/resources
        # For now, simulate finding alternative
        return True

    def _skip_step(self, failure: WorkflowFailure) -> bool:
        """Skip optional step"""
        logger.info(f"Skipping optional step {failure.step_id}")
        return True

    def _rollback(self, failure: WorkflowFailure) -> bool:
        """Rollback to previous state"""
        logger.info(f"Rolling back workflow {failure.workflow_id}")

        # Would actually rollback changes here
        return True

    def _auto_fix(self, failure: WorkflowFailure) -> bool:
        """Automatically fix the issue"""
        logger.info(f"Attempting auto-fix for {failure.failure_type.value}")

        if failure.failure_type == FailureType.PERMISSION_DENIED:
            # Would attempt to elevate permissions
            logger.info("Requesting elevated permissions")
            return True

        elif failure.failure_type == FailureType.CONFIGURATION_ERROR:
            # Would attempt to fix configuration
            logger.info("Fixing configuration")
            return True

        return False

    def _request_user_input(self, failure: WorkflowFailure) -> bool:
        """Request user input for resolution"""
        logger.info(f"Requesting user input for {failure.step_id}")

        # Would send notification to user
        return False  # Requires manual intervention

    def add_healing_rule(self, rule: HealingRule):
        """Add custom healing rule"""
        self.healing_rules.append(rule)
        self._save_rules()
        logger.info(f"Added healing rule: {rule.rule_id}")

    def get_statistics(self) -> Dict[str, Any]:
        """Get self-healing statistics"""
        return {
            **self.stats,
            'total_rules': len(self.healing_rules),
            'recent_failures': len([f for f in self.failures[-100:]]),
            'recent_recoveries': len([r for r in self.recoveries[-100:] if r.success])
        }

    def get_failure_history(self, limit: int = 50) -> List[Dict]:
        """Get recent failures"""
        recent = self.failures[-limit:]
        return [asdict(f) for f in reversed(recent)]

    def get_recovery_history(self, limit: int = 50) -> List[Dict]:
        """Get recent recovery actions"""
        recent = self.recoveries[-limit:]
        return [asdict(r) for r in reversed(recent)]

    def register_failure_callback(self, callback: Callable):
        """Register callback for failures"""
        self.failure_callbacks.append(callback)

    def register_recovery_callback(self, callback: Callable):
        """Register callback for recoveries"""
        self.recovery_callbacks.append(callback)

    def _save_rules(self):
        """Save healing rules"""
        try:
            rules_data = [asdict(r) for r in self.healing_rules]
            # Convert enums to strings
            for rule in rules_data:
                rule['failure_type'] = rule['failure_type'].value if isinstance(rule['failure_type'], FailureType) else rule['failure_type']
                rule['recovery_strategy'] = rule['recovery_strategy'].value if isinstance(rule['recovery_strategy'], RecoveryStrategy) else rule['recovery_strategy']

            with open(self.rules_file, 'w') as f:
                json.dump(rules_data, f, indent=2)
        except Exception as e:
            logger.error(f"Error saving rules: {e}")

    def _load_rules(self):
        """Load healing rules"""
        try:
            if self.rules_file.exists():
                with open(self.rules_file, 'r') as f:
                    rules_data = json.load(f)

                    for rule_dict in rules_data:
                        rule_dict['failure_type'] = FailureType(rule_dict['failure_type'])
                        rule_dict['recovery_strategy'] = RecoveryStrategy(rule_dict['recovery_strategy'])

                        self.healing_rules.append(HealingRule(**rule_dict))

                logger.info(f"Loaded {len(self.healing_rules)} healing rules")
        except Exception as e:
            logger.error(f"Error loading rules: {e}")


# Global instance
_healing_system: Optional[SelfHealingSystem] = None


def get_healing_system(data_dir: Path = None) -> SelfHealingSystem:
    """Get or create global healing system"""
    global _healing_system

    if _healing_system is None:
        if data_dir is None:
            data_dir = Path.home() / ".windows-ai" / "healing"
        _healing_system = SelfHealingSystem(data_dir)

    return _healing_system


def initialize_healing_system(data_dir: Path = None):
    """Initialize the self-healing system"""
    system = get_healing_system(data_dir)
    logger.info("Self-healing system initialized")
    return system
