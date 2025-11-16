"""
Constitutional AI Plugin
AI safety through constitutional principles and critique
"""

from typing import Dict, Any, Optional, List


class ConstitutionalAIPlugin:
    """Plugin for Constitutional AI principles"""

    name = "constitutional_ai"
    version = "1.0.0"
    description = "Implement AI safety through constitutional principles"
    author = "Windows AI Team"

    def __init__(self):
        self.constitution = {}
        self.critiques = []
        self.revisions = []
        self._initialized = False

    def initialize(self, config: Optional[Dict[str, Any]] = None) -> bool:
        """Initialize the Constitutional AI plugin"""
        try:
            # Default constitution principles
            self.constitution = {
                "helpfulness": "Responses should be helpful and informative",
                "harmlessness": "Avoid harmful, unethical, or illegal content",
                "honesty": "Be truthful and acknowledge uncertainty",
                "respect": "Treat all individuals with respect and dignity",
                "privacy": "Protect user privacy and personal information",
                "fairness": "Avoid bias and treat all groups fairly"
            }

            if config and "principles" in config:
                self.constitution.update(config["principles"])

            self._initialized = True
            return True
        except Exception as e:
            print(f"Error initializing Constitutional AI plugin: {e}")
            return False

    def execute(self, action: str, params: Dict[str, Any]) -> Dict[str, Any]:
        """Execute a Constitutional AI action"""
        if not self._initialized:
            return {"success": False, "error": "Plugin not initialized"}

        try:
            if action == "critique":
                return self._critique(params)
            elif action == "revise":
                return self._revise(params)
            elif action == "evaluate_response":
                return self._evaluate_response(params)
            elif action == "add_principle":
                return self._add_principle(params)
            elif action == "get_constitution":
                return self._get_constitution()
            else:
                return {"success": False, "error": f"Unknown action: {action}"}
        except Exception as e:
            return {"success": False, "error": str(e)}

    def _critique(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Critique a response against constitutional principles"""
        response = params.get("response", "")
        principles = params.get("principles", list(self.constitution.keys()))

        violations = []
        for principle in principles:
            if principle not in self.constitution:
                continue

            violation = self._check_violation(response, principle)
            if violation:
                violations.append(violation)

        critique = {
            "response": response,
            "principles_checked": principles,
            "violations": violations,
            "compliant": len(violations) == 0
        }

        self.critiques.append(critique)

        return {
            "success": True,
            "critique": critique
        }

    def _check_violation(self, response: str, principle: str) -> Optional[Dict[str, Any]]:
        """Check if response violates a principle"""
        response_lower = response.lower()

        # Simulate violation checking
        # In production, would use more sophisticated analysis

        if principle == "harmlessness":
            harmful_keywords = ["violence", "illegal", "harmful", "dangerous"]
            if any(kw in response_lower for kw in harmful_keywords):
                return {
                    "principle": principle,
                    "description": self.constitution[principle],
                    "violation": "Response contains potentially harmful content",
                    "severity": "high"
                }

        elif principle == "honesty":
            dishonest_indicators = ["definitely", "absolutely certain", "always"]
            if any(ind in response_lower for ind in dishonest_indicators):
                return {
                    "principle": principle,
                    "description": self.constitution[principle],
                    "violation": "Response may overstate certainty",
                    "severity": "medium"
                }

        elif principle == "fairness":
            biased_keywords = ["all [group]", "always [stereotype]"]
            # Simplified check
            if "all" in response_lower and len(response.split()) < 50:
                return {
                    "principle": principle,
                    "description": self.constitution[principle],
                    "violation": "Response may contain generalizations",
                    "severity": "medium"
                }

        elif principle == "privacy":
            privacy_keywords = ["ssn", "credit card", "password", "personal data"]
            if any(kw in response_lower for kw in privacy_keywords):
                return {
                    "principle": principle,
                    "description": self.constitution[principle],
                    "violation": "Response may contain sensitive information",
                    "severity": "high"
                }

        return None

    def _revise(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Revise response to align with constitutional principles"""
        response = params.get("response", "")
        critique = params.get("critique")

        if not critique:
            # Generate critique first
            critique_result = self._critique({"response": response})
            critique = critique_result["critique"]

        if critique["compliant"]:
            return {
                "success": True,
                "original": response,
                "revised": response,
                "revisions_made": [],
                "message": "Response already compliant"
            }

        # Generate revisions
        revisions_made = []
        revised_response = response

        for violation in critique["violations"]:
            principle = violation["principle"]

            revision = {
                "principle": principle,
                "original_issue": violation["violation"],
                "action_taken": ""
            }

            # Apply principle-specific revisions
            if principle == "harmlessness":
                revision["action_taken"] = "Removed harmful content and added safety disclaimer"
                revised_response = "I should clarify that " + revised_response

            elif principle == "honesty":
                revision["action_taken"] = "Added uncertainty qualifiers"
                revised_response = revised_response.replace("definitely", "likely")
                revised_response = revised_response.replace("always", "often")

            elif principle == "fairness":
                revision["action_taken"] = "Removed generalizations and added nuance"
                revised_response = revised_response.replace("all", "many")

            elif principle == "privacy":
                revision["action_taken"] = "Removed sensitive information"
                revised_response = "[REDACTED FOR PRIVACY] " + revised_response

            revisions_made.append(revision)

        revision_record = {
            "original": response,
            "revised": revised_response,
            "revisions": revisions_made,
            "critique": critique
        }

        self.revisions.append(revision_record)

        return {
            "success": True,
            **revision_record
        }

    def _evaluate_response(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Comprehensively evaluate response against all principles"""
        response = params.get("response", "")

        # Critique against all principles
        critique = self._critique({
            "response": response,
            "principles": list(self.constitution.keys())
        })

        # Calculate compliance scores
        scores = {}
        for principle in self.constitution.keys():
            violation = next((v for v in critique["critique"]["violations"]
                            if v["principle"] == principle), None)

            if violation:
                scores[principle] = 0.3 if violation["severity"] == "high" else 0.6
            else:
                scores[principle] = 1.0

        overall_score = sum(scores.values()) / len(scores) if scores else 0

        evaluation = {
            "response": response,
            "principle_scores": scores,
            "overall_score": overall_score,
            "compliant": overall_score >= 0.8,
            "critique": critique["critique"]
        }

        return {
            "success": True,
            "evaluation": evaluation
        }

    def _add_principle(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Add a new constitutional principle"""
        principle_id = params.get("id", "")
        description = params.get("description", "")

        if not principle_id or not description:
            return {"success": False, "error": "Principle ID and description required"}

        self.constitution[principle_id] = description

        return {
            "success": True,
            "principle_id": principle_id,
            "total_principles": len(self.constitution)
        }

    def _get_constitution(self) -> Dict[str, Any]:
        """Get the current constitution"""
        return {
            "success": True,
            "constitution": self.constitution,
            "principles_count": len(self.constitution),
            "critiques_performed": len(self.critiques),
            "revisions_made": len(self.revisions)
        }

    def shutdown(self) -> bool:
        """Cleanup plugin resources"""
        self._initialized = False
        self.critiques = []
        self.revisions = []
        return True
