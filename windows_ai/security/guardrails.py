"""
Guardrails Manager for Windows AI
Content filtering, safety checks, and policy enforcement
"""

import asyncio
import logging
import re
from typing import Dict, List, Any, Optional, Callable
from dataclasses import dataclass, field
from enum import Enum

logger = logging.getLogger(__name__)

class GuardrailLevel(Enum):
    OFF = "off"
    MINIMAL = "minimal"
    STANDARD = "standard"
    STRICT = "strict"

@dataclass
class GuardrailPolicy:
    name: str
    description: str
    enabled: bool = True
    level: GuardrailLevel = GuardrailLevel.STANDARD
    patterns: List[str] = field(default_factory=list)
    action: str = "block"  # block, warn, log

class GuardrailsManager:
    """Manages content guardrails and safety policies"""

    def __init__(self):
        self.policies: Dict[str, GuardrailPolicy] = {}
        self.level: GuardrailLevel = GuardrailLevel.STANDARD
        self.custom_validators: List[Callable] = []
        self._initialized = False

    async def initialize(self, config: Optional[Dict[str, Any]] = None):
        """Initialize guardrails"""
        if self._initialized:
            return

        if config:
            level = config.get("level", "standard")
            self.level = GuardrailLevel(level)

        # Register default policies
        self._register_default_policies()

        self._initialized = True
        logger.info(f"Guardrails initialized with level: {self.level.value}")

    def _register_default_policies(self):
        """Register default guardrail policies"""
        # Harmful content policy
        self.register_policy(GuardrailPolicy(
            name="harmful_content",
            description="Block potentially harmful content generation",
            patterns=[
                r"(create|make|build)\s+(virus|malware|trojan|ransomware)",
                r"(hack|exploit|attack)\s+.*(server|website|system)",
                r"(bomb|weapon|explosive)\s+(instructions|how\s+to)",
            ],
            action="block"
        ))

        # Personal data policy
        self.register_policy(GuardrailPolicy(
            name="personal_data",
            description="Protect personal identifiable information",
            patterns=[
                r"\b\d{3}-\d{2}-\d{4}\b",  # SSN
                r"\b\d{16}\b",  # Credit card
                r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b",  # Email (for logging)
            ],
            action="warn"
        ))

        # Code safety policy
        self.register_policy(GuardrailPolicy(
            name="dangerous_code",
            description="Flag potentially dangerous code patterns",
            patterns=[
                r"rm\s+-rf\s+/",
                r"format\s+[a-zA-Z]:",
                r"del\s+/[sS]",
                r"DROP\s+DATABASE",
                r"TRUNCATE\s+TABLE",
                r"exec\s*\(\s*['\"]",
                r"eval\s*\(\s*['\"]",
            ],
            action="warn"
        ))

        # Credential exposure policy
        self.register_policy(GuardrailPolicy(
            name="credentials",
            description="Prevent credential exposure",
            patterns=[
                r"(password|passwd|pwd)\s*[=:]\s*['\"][^'\"]+['\"]",
                r"(api_key|apikey|secret)\s*[=:]\s*['\"][^'\"]+['\"]",
                r"(token|bearer)\s*[=:]\s*['\"][^'\"]+['\"]",
                r"-----BEGIN\s+(RSA\s+)?PRIVATE\s+KEY-----",
            ],
            action="block"
        ))

        # System command policy
        self.register_policy(GuardrailPolicy(
            name="system_commands",
            description="Control system command execution",
            patterns=[
                r"shutdown\s+/[srh]",
                r"reboot",
                r"halt",
                r"init\s+0",
            ],
            action="block"
        ))

    def register_policy(self, policy: GuardrailPolicy):
        """Register a guardrail policy"""
        self.policies[policy.name] = policy
        logger.debug(f"Registered guardrail policy: {policy.name}")

    def add_custom_validator(self, validator: Callable[[str], tuple]):
        """Add a custom validation function"""
        self.custom_validators.append(validator)

    def set_level(self, level: GuardrailLevel):
        """Set guardrail level"""
        self.level = level
        logger.info(f"Guardrail level set to: {level.value}")

    def enable_policy(self, policy_name: str):
        """Enable a specific policy"""
        if policy_name in self.policies:
            self.policies[policy_name].enabled = True

    def disable_policy(self, policy_name: str):
        """Disable a specific policy"""
        if policy_name in self.policies:
            self.policies[policy_name].enabled = False

    async def check_content(
        self,
        content: str,
        context: Optional[str] = None
    ) -> Dict[str, Any]:
        """Check content against all guardrails"""
        if self.level == GuardrailLevel.OFF:
            return {"allowed": True, "violations": [], "warnings": []}

        violations = []
        warnings = []

        # Check against all enabled policies
        for policy_name, policy in self.policies.items():
            if not policy.enabled:
                continue

            for pattern in policy.patterns:
                try:
                    if re.search(pattern, content, re.IGNORECASE):
                        violation = {
                            "policy": policy_name,
                            "pattern": pattern,
                            "action": policy.action,
                            "description": policy.description
                        }

                        if policy.action == "block":
                            violations.append(violation)
                        elif policy.action == "warn":
                            warnings.append(violation)
                        elif policy.action == "log":
                            logger.warning(f"Guardrail log: {policy_name} triggered")
                except re.error as e:
                    logger.error(f"Invalid regex pattern in policy {policy_name}: {e}")

        # Run custom validators
        for validator in self.custom_validators:
            try:
                valid, message = validator(content)
                if not valid:
                    violations.append({
                        "policy": "custom",
                        "description": message,
                        "action": "block"
                    })
            except Exception as e:
                logger.error(f"Custom validator error: {e}")

        # Determine if content is allowed
        allowed = len(violations) == 0

        return {
            "allowed": allowed,
            "violations": violations,
            "warnings": warnings,
            "checked_policies": len(self.policies),
            "level": self.level.value
        }

    async def filter_response(
        self,
        response: str,
        redact: bool = True
    ) -> str:
        """Filter and potentially redact a response"""
        if self.level == GuardrailLevel.OFF:
            return response

        filtered = response

        # Redact sensitive patterns
        redact_patterns = [
            (r"\b\d{3}-\d{2}-\d{4}\b", "[SSN REDACTED]"),
            (r"\b\d{16}\b", "[CARD REDACTED]"),
            (r"-----BEGIN\s+(RSA\s+)?PRIVATE\s+KEY-----[\s\S]*?-----END\s+(RSA\s+)?PRIVATE\s+KEY-----", "[KEY REDACTED]"),
            (r"(password|passwd|pwd)\s*[=:]\s*['\"][^'\"]+['\"]", r"\1=[REDACTED]"),
            (r"(api_key|apikey|secret|token)\s*[=:]\s*['\"][^'\"]+['\"]", r"\1=[REDACTED]"),
        ]

        if redact:
            for pattern, replacement in redact_patterns:
                try:
                    filtered = re.sub(pattern, replacement, filtered, flags=re.IGNORECASE)
                except re.error:
                    pass

        return filtered

    def get_policies(self) -> List[Dict[str, Any]]:
        """Get all registered policies"""
        return [
            {
                "name": p.name,
                "description": p.description,
                "enabled": p.enabled,
                "action": p.action,
                "pattern_count": len(p.patterns)
            }
            for p in self.policies.values()
        ]

    def get_config(self) -> Dict[str, Any]:
        """Get current guardrails configuration"""
        return {
            "level": self.level.value,
            "policy_count": len(self.policies),
            "enabled_policies": sum(1 for p in self.policies.values() if p.enabled),
            "custom_validators": len(self.custom_validators)
        }
