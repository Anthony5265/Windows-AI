"""
Explainable AI (XAI) Module
Provides transparency and explanations for AI decisions and actions
"""
import logging
from typing import Dict, List, Any, Optional
from dataclasses import dataclass, asdict
from datetime import datetime
from enum import Enum
from pathlib import Path
import json

logger = logging.getLogger(__name__)


class ActionType(Enum):
    """Types of AI actions that can be explained"""
    CHAT_RESPONSE = "chat_response"
    FILE_OPERATION = "file_operation"
    SYSTEM_COMMAND = "system_command"
    AUTOMATION = "automation"
    RECOMMENDATION = "recommendation"
    PREDICTION = "prediction"
    CONFIGURATION_CHANGE = "configuration_change"


class RiskLevel(Enum):
    """Risk levels for actions"""
    SAFE = "safe"  # No confirmation needed
    LOW = "low"  # Optional confirmation
    MEDIUM = "medium"  # Recommended confirmation
    HIGH = "high"  # Required confirmation
    CRITICAL = "critical"  # Strict confirmation + explanation


@dataclass
class ActionExplanation:
    """Explanation for an AI action"""
    action_id: str
    action_type: ActionType
    timestamp: str
    description: str
    reasoning: str
    risk_level: RiskLevel
    requires_confirmation: bool
    inputs: Dict[str, Any]
    expected_outcome: str
    alternatives_considered: List[str]
    confidence: float  # 0-1
    data_sources: List[str]
    impact_analysis: str


@dataclass
class ActionLog:
    """Log of executed action"""
    action_id: str
    explanation: ActionExplanation
    user_approved: bool
    execution_time: str
    success: bool
    actual_outcome: str
    user_feedback: Optional[str]


class ExplainableAI:
    """
    Manages explainability for AI decisions and actions

    Features:
    - Generate explanations for all AI actions
    - Risk assessment for actions
    - User confirmation for sensitive operations
    - Action logging and audit trail
    - "Why did you do that?" capability
    - Learning from user feedback
    """

    def __init__(self, data_dir: Path):
        self.data_dir = data_dir
        self.data_dir.mkdir(parents=True, exist_ok=True)

        self.action_log_file = data_dir / "action_log.json"
        self.action_logs: List[ActionLog] = []

        # Configuration for risk assessment
        self.risk_rules = self._initialize_risk_rules()

        # Load existing logs
        self._load_logs()

    def _initialize_risk_rules(self) -> Dict[str, Any]:
        """Initialize rules for risk assessment"""
        return {
            "file_operations": {
                "read": RiskLevel.SAFE,
                "write": RiskLevel.LOW,
                "delete": RiskLevel.HIGH,
                "move": RiskLevel.MEDIUM,
                "rename": RiskLevel.LOW,
            },
            "system_commands": {
                "query": RiskLevel.SAFE,
                "modify_settings": RiskLevel.HIGH,
                "install_software": RiskLevel.CRITICAL,
                "uninstall_software": RiskLevel.HIGH,
                "restart": RiskLevel.MEDIUM,
                "shutdown": RiskLevel.MEDIUM,
            },
            "sensitive_paths": [
                "C:\\Windows\\System32",
                "C:\\Program Files",
                "/usr/bin",
                "/etc",
            ]
        }

    def create_explanation(
        self,
        action_type: ActionType,
        description: str,
        reasoning: str,
        inputs: Dict[str, Any],
        expected_outcome: str,
        alternatives: List[str] = None,
        confidence: float = 0.9,
        data_sources: List[str] = None
    ) -> ActionExplanation:
        """
        Create an explanation for an AI action

        Args:
            action_type: Type of action being taken
            description: Human-readable description
            reasoning: Why the AI chose this action
            inputs: Input data used for decision
            expected_outcome: What the AI expects to happen
            alternatives: Other options that were considered
            confidence: AI's confidence in this decision (0-1)
            data_sources: What data informed this decision

        Returns:
            ActionExplanation object
        """
        import uuid

        action_id = str(uuid.uuid4())

        # Assess risk
        risk_level = self._assess_risk(action_type, inputs, description)

        # Determine if confirmation is required
        requires_confirmation = risk_level in [RiskLevel.HIGH, RiskLevel.CRITICAL]

        # Generate impact analysis
        impact_analysis = self._analyze_impact(action_type, inputs, expected_outcome)

        explanation = ActionExplanation(
            action_id=action_id,
            action_type=action_type,
            timestamp=datetime.now().isoformat(),
            description=description,
            reasoning=reasoning,
            risk_level=risk_level,
            requires_confirmation=requires_confirmation,
            inputs=inputs,
            expected_outcome=expected_outcome,
            alternatives_considered=alternatives or [],
            confidence=confidence,
            data_sources=data_sources or ["user_input"],
            impact_analysis=impact_analysis
        )

        logger.info(f"Created explanation for {action_type.value}: {description}")
        return explanation

    def _assess_risk(self, action_type: ActionType, inputs: Dict[str, Any], description: str) -> RiskLevel:
        """Assess risk level of an action"""

        # Default risk levels by action type
        type_risk = {
            ActionType.CHAT_RESPONSE: RiskLevel.SAFE,
            ActionType.RECOMMENDATION: RiskLevel.SAFE,
            ActionType.PREDICTION: RiskLevel.SAFE,
            ActionType.AUTOMATION: RiskLevel.MEDIUM,
            ActionType.FILE_OPERATION: RiskLevel.LOW,
            ActionType.SYSTEM_COMMAND: RiskLevel.HIGH,
            ActionType.CONFIGURATION_CHANGE: RiskLevel.MEDIUM,
        }

        base_risk = type_risk.get(action_type, RiskLevel.MEDIUM)

        # Elevate risk based on specific patterns
        if action_type == ActionType.FILE_OPERATION:
            operation = inputs.get("operation", "").lower()
            path = inputs.get("path", "")

            # Check operation type
            op_risk = self.risk_rules["file_operations"].get(operation, RiskLevel.MEDIUM)

            # Check if sensitive path
            if any(sensitive in path for sensitive in self.risk_rules["sensitive_paths"]):
                # Elevate one level
                risk_levels = list(RiskLevel)
                current_idx = risk_levels.index(op_risk)
                op_risk = risk_levels[min(current_idx + 1, len(risk_levels) - 1)]

            return op_risk

        elif action_type == ActionType.SYSTEM_COMMAND:
            command_type = inputs.get("command_type", "").lower()
            return self.risk_rules["system_commands"].get(command_type, RiskLevel.HIGH)

        # Check for destructive keywords
        destructive_keywords = ["delete", "remove", "uninstall", "format", "wipe", "clear"]
        if any(keyword in description.lower() for keyword in destructive_keywords):
            risk_levels = list(RiskLevel)
            current_idx = risk_levels.index(base_risk)
            return risk_levels[min(current_idx + 2, len(risk_levels) - 1)]

        return base_risk

    def _analyze_impact(self, action_type: ActionType, inputs: Dict[str, Any], expected_outcome: str) -> str:
        """Analyze the impact of an action"""

        impact_parts = []

        # Scope analysis
        if action_type == ActionType.FILE_OPERATION:
            path = inputs.get("path", "")
            operation = inputs.get("operation", "")

            if operation == "delete":
                impact_parts.append(f"⚠️  Will permanently remove: {path}")
            elif operation == "move":
                impact_parts.append(f"📁 Will relocate file from current location")
            elif operation == "write":
                impact_parts.append(f"✏️  Will modify or create file")

        # Reversibility
        reversible_actions = [ActionType.CHAT_RESPONSE, ActionType.RECOMMENDATION]
        if action_type in reversible_actions:
            impact_parts.append("✅ This action is fully reversible")
        else:
            impact_parts.append("⚠️  This action may not be easily reversible")

        # Expected outcome
        impact_parts.append(f"Expected result: {expected_outcome}")

        return " | ".join(impact_parts)

    def request_confirmation(self, explanation: ActionExplanation) -> Dict[str, Any]:
        """
        Format action explanation for user confirmation

        Returns a structured confirmation request
        """
        confirmation_request = {
            "action_id": explanation.action_id,
            "title": f"Confirm: {explanation.description}",
            "risk_level": explanation.risk_level.value,
            "message": explanation.reasoning,
            "details": {
                "expected_outcome": explanation.expected_outcome,
                "impact": explanation.impact_analysis,
                "confidence": f"{explanation.confidence * 100:.0f}%",
                "alternatives": explanation.alternatives_considered
            },
            "data_sources": explanation.data_sources,
            "requires_approval": explanation.requires_confirmation,
            "timestamp": explanation.timestamp
        }

        return confirmation_request

    def log_action(
        self,
        explanation: ActionExplanation,
        user_approved: bool,
        success: bool,
        actual_outcome: str,
        user_feedback: Optional[str] = None
    ):
        """Log an executed action"""

        log_entry = ActionLog(
            action_id=explanation.action_id,
            explanation=explanation,
            user_approved=user_approved,
            execution_time=datetime.now().isoformat(),
            success=success,
            actual_outcome=actual_outcome,
            user_feedback=user_feedback
        )

        self.action_logs.append(log_entry)

        # Save logs
        self._save_logs()

        logger.info(f"Logged action {explanation.action_id}: success={success}")

    def get_action_history(self, limit: int = 50, action_type: Optional[ActionType] = None) -> List[Dict]:
        """Get action history, optionally filtered by type"""

        logs = self.action_logs

        if action_type:
            logs = [log for log in logs if log.explanation.action_type == action_type]

        # Return most recent first
        recent_logs = list(reversed(logs))[:limit]

        return [self._log_to_dict(log) for log in recent_logs]

    def explain_past_action(self, action_id: str) -> Optional[Dict[str, Any]]:
        """
        Explain a past action - "Why did you do that?"

        Args:
            action_id: ID of the action to explain

        Returns:
            Detailed explanation of the action
        """
        for log in self.action_logs:
            if log.action_id == action_id:
                return {
                    "action": self._explanation_to_dict(log.explanation),
                    "execution": {
                        "approved": log.user_approved,
                        "time": log.execution_time,
                        "success": log.success,
                        "outcome": log.actual_outcome,
                        "feedback": log.user_feedback
                    },
                    "explanation_summary": self._generate_summary(log)
                }

        return None

    def _generate_summary(self, log: ActionLog) -> str:
        """Generate a natural language summary of an action"""

        exp = log.explanation
        summary_parts = [
            f"At {exp.timestamp}, I performed: {exp.description}.",
            f"My reasoning was: {exp.reasoning}.",
            f"I expected: {exp.expected_outcome}.",
        ]

        if log.success:
            summary_parts.append(f"The action succeeded. Actual outcome: {log.actual_outcome}.")
        else:
            summary_parts.append(f"The action failed. Actual outcome: {log.actual_outcome}.")

        if exp.alternatives_considered:
            alternatives_str = ", ".join(exp.alternatives_considered)
            summary_parts.append(f"I also considered: {alternatives_str}.")

        summary_parts.append(f"My confidence was {exp.confidence * 100:.0f}%.")

        return " ".join(summary_parts)

    def _explanation_to_dict(self, exp: ActionExplanation) -> Dict:
        """Convert explanation to dict"""
        d = asdict(exp)
        d["action_type"] = exp.action_type.value
        d["risk_level"] = exp.risk_level.value
        return d

    def _log_to_dict(self, log: ActionLog) -> Dict:
        """Convert log to dict"""
        return {
            "action_id": log.action_id,
            "explanation": self._explanation_to_dict(log.explanation),
            "user_approved": log.user_approved,
            "execution_time": log.execution_time,
            "success": log.success,
            "actual_outcome": log.actual_outcome,
            "user_feedback": log.user_feedback
        }

    def _save_logs(self):
        """Save action logs to file"""
        try:
            logs_dict = [self._log_to_dict(log) for log in self.action_logs]
            with open(self.action_log_file, 'w') as f:
                json.dump(logs_dict, f, indent=2)
        except Exception as e:
            logger.error(f"Error saving action logs: {e}")

    def _load_logs(self):
        """Load action logs from file"""
        try:
            if self.action_log_file.exists():
                with open(self.action_log_file, 'r') as f:
                    logs_dict = json.load(f)

                # Reconstruct logs
                for log_dict in logs_dict:
                    exp_dict = log_dict["explanation"]
                    exp_dict["action_type"] = ActionType(exp_dict["action_type"])
                    exp_dict["risk_level"] = RiskLevel(exp_dict["risk_level"])

                    explanation = ActionExplanation(**exp_dict)

                    log_entry = ActionLog(
                        action_id=log_dict["action_id"],
                        explanation=explanation,
                        user_approved=log_dict["user_approved"],
                        execution_time=log_dict["execution_time"],
                        success=log_dict["success"],
                        actual_outcome=log_dict["actual_outcome"],
                        user_feedback=log_dict.get("user_feedback")
                    )

                    self.action_logs.append(log_entry)

                logger.info(f"Loaded {len(self.action_logs)} action logs")
        except Exception as e:
            logger.error(f"Error loading action logs: {e}")


# Global instance
_xai_system: Optional[ExplainableAI] = None


def get_xai_system(data_dir: Path = None) -> ExplainableAI:
    """Get or create global XAI system"""
    global _xai_system

    if _xai_system is None:
        if data_dir is None:
            data_dir = Path.home() / ".windows-ai" / "xai"
        _xai_system = ExplainableAI(data_dir)

    return _xai_system


def initialize_xai_system(data_dir: Path = None):
    """Initialize the XAI system"""
    system = get_xai_system(data_dir)
    logger.info("Explainable AI system initialized")
    return system
