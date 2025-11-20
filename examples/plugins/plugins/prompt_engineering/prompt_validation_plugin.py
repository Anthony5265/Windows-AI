"""
Prompt Validation Plugin
Validate and score prompt quality before sending to LLMs
"""

from typing import Dict, Any, Optional, List
import re


class PromptValidationPlugin:
    """Plugin for prompt validation and quality scoring"""

    name = "prompt_validation"
    version = "1.0.0"
    description = "Validate prompt quality and detect common issues"
    author = "Windows AI Team"

    def __init__(self):
        self.validation_rules = {}
        self.quality_metrics = {}
        self.validation_history = []
        self._initialized = False

    def initialize(self, config: Optional[Dict[str, Any]] = None) -> bool:
        """Initialize the Prompt Validation plugin"""
        try:
            # Initialize validation rules
            self.validation_rules = {
                "clarity": {
                    "check_ambiguity": True,
                    "check_specificity": True,
                    "min_length": 10
                },
                "structure": {
                    "check_formatting": True,
                    "check_sections": True
                },
                "completeness": {
                    "check_context": True,
                    "check_examples": False
                },
                "safety": {
                    "check_harmful_content": True,
                    "check_bias": True
                }
            }
            self._initialized = True
            return True
        except Exception as e:
            print(f"Error initializing Prompt Validation plugin: {e}")
            return False

    def execute(self, action: str, params: Dict[str, Any]) -> Dict[str, Any]:
        """Execute a Prompt Validation action"""
        if not self._initialized:
            return {"success": False, "error": "Plugin not initialized"}

        try:
            if action == "validate":
                return self._validate(params)
            elif action == "score_quality":
                return self._score_quality(params)
            elif action == "check_clarity":
                return self._check_clarity(params)
            elif action == "check_safety":
                return self._check_safety(params)
            elif action == "suggest_improvements":
                return self._suggest_improvements(params)
            elif action == "compare_prompts":
                return self._compare_prompts(params)
            elif action == "detect_issues":
                return self._detect_issues(params)
            else:
                return {"success": False, "error": f"Unknown action: {action}"}
        except Exception as e:
            return {"success": False, "error": str(e)}

    def _validate(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Comprehensive prompt validation"""
        prompt = params.get("prompt", "")
        validation_level = params.get("level", "standard")  # basic, standard, strict

        validation_results = {
            "is_valid": True,
            "score": 0.0,
            "issues": [],
            "warnings": [],
            "passed_checks": [],
            "failed_checks": []
        }

        # Basic checks
        if not prompt or not prompt.strip():
            validation_results["is_valid"] = False
            validation_results["failed_checks"].append("empty_prompt")
            validation_results["issues"].append("Prompt is empty")
            return {"success": True, "validation": validation_results}

        # Length checks
        if len(prompt) < self.validation_rules["clarity"]["min_length"]:
            validation_results["warnings"].append(f"Prompt is very short ({len(prompt)} chars)")
        else:
            validation_results["passed_checks"].append("minimum_length")

        # Clarity checks
        clarity_result = self._check_clarity({"prompt": prompt})
        if not clarity_result["success"]:
            validation_results["issues"].extend(clarity_result.get("issues", []))
            validation_results["failed_checks"].append("clarity")
        else:
            validation_results["passed_checks"].append("clarity")
            if clarity_result.get("warnings"):
                validation_results["warnings"].extend(clarity_result["warnings"])

        # Structure checks
        structure_result = self._check_structure(prompt)
        if structure_result["has_structure"]:
            validation_results["passed_checks"].append("structure")
        else:
            validation_results["warnings"].append("No clear structure detected")

        # Safety checks (only in standard/strict mode)
        if validation_level in ["standard", "strict"]:
            safety_result = self._check_safety({"prompt": prompt})
            if not safety_result["is_safe"]:
                validation_results["is_valid"] = False
                validation_results["failed_checks"].append("safety")
                validation_results["issues"].extend(safety_result["concerns"])
            else:
                validation_results["passed_checks"].append("safety")

        # Completeness checks (only in strict mode)
        if validation_level == "strict":
            completeness_result = self._check_completeness(prompt)
            if not completeness_result["is_complete"]:
                validation_results["warnings"].extend(completeness_result["missing_elements"])

        # Calculate overall score
        total_checks = len(validation_results["passed_checks"]) + len(validation_results["failed_checks"])
        if total_checks > 0:
            validation_results["score"] = len(validation_results["passed_checks"]) / total_checks
        else:
            validation_results["score"] = 0.5

        # Determine if valid
        if validation_results["failed_checks"] or validation_results["issues"]:
            validation_results["is_valid"] = False

        # Store in history
        self.validation_history.append({
            "prompt": prompt[:100] + "..." if len(prompt) > 100 else prompt,
            "validation_level": validation_level,
            "score": validation_results["score"],
            "is_valid": validation_results["is_valid"],
            "timestamp": "now"
        })

        return {
            "success": True,
            "validation": validation_results
        }

    def _score_quality(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Score prompt quality on multiple dimensions"""
        prompt = params.get("prompt", "")

        if not prompt:
            return {"success": False, "error": "No prompt provided"}

        quality_scores = {
            "clarity": 0.0,
            "specificity": 0.0,
            "structure": 0.0,
            "completeness": 0.0,
            "effectiveness": 0.0,
            "overall": 0.0
        }

        # Clarity score
        clarity_indicators = {
            "has_clear_task": any(word in prompt.lower() for word in ["task:", "please", "instruction:", "do"]),
            "has_question": "?" in prompt,
            "has_imperative": any(word in prompt.lower() for word in ["create", "write", "explain", "describe", "analyze"]),
            "reasonable_length": 20 < len(prompt) < 2000
        }
        quality_scores["clarity"] = sum(clarity_indicators.values()) / len(clarity_indicators)

        # Specificity score
        specificity_indicators = {
            "has_details": len(prompt.split()) > 15,
            "has_constraints": any(word in prompt.lower() for word in ["must", "should", "constraint", "requirement"]),
            "has_examples": "example" in prompt.lower() or "such as" in prompt.lower(),
            "has_format": any(word in prompt.lower() for word in ["format", "structure", "output"])
        }
        quality_scores["specificity"] = sum(specificity_indicators.values()) / len(specificity_indicators)

        # Structure score
        structure_result = self._check_structure(prompt)
        quality_scores["structure"] = structure_result["structure_score"]

        # Completeness score
        completeness_result = self._check_completeness(prompt)
        quality_scores["completeness"] = completeness_result["completeness_score"]

        # Effectiveness score (combination)
        quality_scores["effectiveness"] = (
            quality_scores["clarity"] * 0.3 +
            quality_scores["specificity"] * 0.3 +
            quality_scores["structure"] * 0.2 +
            quality_scores["completeness"] * 0.2
        )

        # Overall score
        quality_scores["overall"] = quality_scores["effectiveness"]

        # Quality rating
        if quality_scores["overall"] >= 0.8:
            rating = "Excellent"
        elif quality_scores["overall"] >= 0.6:
            rating = "Good"
        elif quality_scores["overall"] >= 0.4:
            rating = "Fair"
        else:
            rating = "Poor"

        return {
            "success": True,
            "quality_scores": quality_scores,
            "rating": rating,
            "prompt_length": len(prompt)
        }

    def _check_clarity(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Check prompt clarity"""
        prompt = params.get("prompt", "")

        issues = []
        warnings = []

        # Check for ambiguous language
        ambiguous_words = ["maybe", "perhaps", "possibly", "might", "could", "thing", "stuff"]
        found_ambiguous = [word for word in ambiguous_words if word in prompt.lower()]
        if found_ambiguous:
            warnings.append(f"Ambiguous language detected: {', '.join(found_ambiguous)}")

        # Check for unclear pronouns without antecedents
        pronouns = ["it", "this", "that", "these", "those", "they"]
        # Simplified check - in production would use NLP
        if prompt.lower().startswith(tuple(pronouns)):
            warnings.append("Starts with pronoun without clear antecedent")

        # Check for run-on sentences (simple heuristic)
        sentences = re.split(r'[.!?]+', prompt)
        long_sentences = [s for s in sentences if len(s.split()) > 40]
        if long_sentences:
            warnings.append(f"{len(long_sentences)} very long sentence(s) detected")

        # Check for clear instruction
        if not any(word in prompt.lower() for word in ["please", "task:", "instruction:", "objective:", "do", "create", "write"]):
            warnings.append("No clear instruction or task statement")

        return {
            "success": True,
            "is_clear": len(issues) == 0,
            "issues": issues,
            "warnings": warnings
        }

    def _check_structure(self, prompt: str) -> Dict[str, Any]:
        """Check prompt structure"""
        has_sections = bool(re.search(r'(###|\n\n|---)', prompt))
        has_numbered_list = bool(re.search(r'\n\d+\.', prompt))
        has_bullet_list = bool(re.search(r'\n[-*•]', prompt))
        has_paragraphs = len(prompt.split('\n\n')) > 1

        structure_score = 0.0
        if has_sections:
            structure_score += 0.3
        if has_numbered_list or has_bullet_list:
            structure_score += 0.3
        if has_paragraphs:
            structure_score += 0.2
        if len(prompt.split('\n')) > 2:
            structure_score += 0.2

        return {
            "has_structure": has_sections or has_numbered_list or has_bullet_list,
            "has_sections": has_sections,
            "has_lists": has_numbered_list or has_bullet_list,
            "has_paragraphs": has_paragraphs,
            "structure_score": min(structure_score, 1.0)
        }

    def _check_completeness(self, prompt: str) -> Dict[str, Any]:
        """Check if prompt is complete"""
        elements = {
            "context": any(word in prompt.lower() for word in ["context", "background", "given"]),
            "task": any(word in prompt.lower() for word in ["task", "objective", "goal", "please", "create"]),
            "constraints": any(word in prompt.lower() for word in ["must", "should", "constraint", "requirement", "limit"]),
            "output_format": any(word in prompt.lower() for word in ["format", "output", "structure", "return"])
        }

        missing_elements = [elem for elem, present in elements.items() if not present]

        completeness_score = sum(elements.values()) / len(elements)

        return {
            "is_complete": completeness_score >= 0.5,
            "completeness_score": completeness_score,
            "present_elements": [elem for elem, present in elements.items() if present],
            "missing_elements": missing_elements
        }

    def _check_safety(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Check for potentially unsafe content"""
        prompt = params.get("prompt", "")

        concerns = []

        # Check for harmful intent keywords (simplified)
        harmful_keywords = ["hack", "exploit", "malicious", "illegal", "weapon"]
        found_harmful = [word for word in harmful_keywords if word in prompt.lower()]

        if found_harmful:
            concerns.append(f"Potentially harmful keywords: {', '.join(found_harmful)}")

        # Check for requests to ignore instructions
        ignore_patterns = ["ignore", "disregard", "forget", "override"]
        found_ignore = [word for word in ignore_patterns if word in prompt.lower()]

        if found_ignore and any(word in prompt.lower() for word in ["previous", "above", "instructions", "rules"]):
            concerns.append("Potential prompt injection attempt detected")

        # Check for excessive special characters (potential injection)
        special_char_ratio = sum(1 for c in prompt if not c.isalnum() and not c.isspace()) / len(prompt) if prompt else 0
        if special_char_ratio > 0.3:
            concerns.append("Unusually high ratio of special characters")

        return {
            "success": True,
            "is_safe": len(concerns) == 0,
            "concerns": concerns
        }

    def _suggest_improvements(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Suggest improvements for a prompt"""
        prompt = params.get("prompt", "")

        if not prompt:
            return {"success": False, "error": "No prompt provided"}

        suggestions = []

        # Run all checks
        validation = self._validate({"prompt": prompt, "level": "strict"})["validation"]
        quality = self._score_quality({"prompt": prompt})["quality_scores"]

        # Generate suggestions based on scores
        if quality["clarity"] < 0.6:
            suggestions.append({
                "category": "clarity",
                "suggestion": "Make the task more explicit. Start with clear instruction words like 'Explain', 'Create', or 'Analyze'",
                "priority": "high"
            })

        if quality["specificity"] < 0.6:
            suggestions.append({
                "category": "specificity",
                "suggestion": "Add more details and constraints. Specify desired format, length, or key points to cover",
                "priority": "high"
            })

        if quality["structure"] < 0.5:
            suggestions.append({
                "category": "structure",
                "suggestion": "Organize your prompt with clear sections. Use bullet points or numbered lists",
                "priority": "medium"
            })

        if quality["completeness"] < 0.6:
            suggestions.append({
                "category": "completeness",
                "suggestion": "Include context, clear task, constraints, and desired output format",
                "priority": "high"
            })

        # Add specific improvements from validation
        if validation["warnings"]:
            for warning in validation["warnings"]:
                suggestions.append({
                    "category": "warning",
                    "suggestion": f"Address warning: {warning}",
                    "priority": "medium"
                })

        # Sort by priority
        priority_order = {"high": 0, "medium": 1, "low": 2}
        suggestions.sort(key=lambda x: priority_order.get(x["priority"], 3))

        return {
            "success": True,
            "prompt": prompt,
            "current_quality": quality["overall"],
            "suggestions": suggestions,
            "num_suggestions": len(suggestions)
        }

    def _compare_prompts(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Compare quality of multiple prompts"""
        prompts = params.get("prompts", [])

        if len(prompts) < 2:
            return {"success": False, "error": "Need at least 2 prompts to compare"}

        comparisons = []

        for i, prompt in enumerate(prompts):
            quality = self._score_quality({"prompt": prompt})["quality_scores"]
            validation = self._validate({"prompt": prompt})["validation"]

            comparisons.append({
                "prompt_index": i,
                "prompt_preview": prompt[:50] + "..." if len(prompt) > 50 else prompt,
                "quality_score": quality["overall"],
                "is_valid": validation["is_valid"],
                "issues_count": len(validation["issues"]),
                "warnings_count": len(validation["warnings"])
            })

        # Sort by quality
        comparisons.sort(key=lambda x: x["quality_score"], reverse=True)

        best_prompt = comparisons[0]
        worst_prompt = comparisons[-1]

        return {
            "success": True,
            "comparisons": comparisons,
            "num_prompts": len(prompts),
            "best_prompt_index": best_prompt["prompt_index"],
            "worst_prompt_index": worst_prompt["prompt_index"],
            "quality_range": {
                "best": best_prompt["quality_score"],
                "worst": worst_prompt["quality_score"]
            }
        }

    def _detect_issues(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Detect common prompt issues"""
        prompt = params.get("prompt", "")

        issues = {
            "critical": [],
            "major": [],
            "minor": []
        }

        # Critical issues
        if not prompt.strip():
            issues["critical"].append("Empty prompt")

        # Check for prompt injection
        if any(phrase in prompt.lower() for phrase in ["ignore previous", "disregard above", "new instructions"]):
            issues["critical"].append("Possible prompt injection attempt")

        # Major issues
        if len(prompt) < 10:
            issues["major"].append("Prompt too short to be effective")

        if len(prompt.split()) > 500:
            issues["major"].append("Prompt may be too long - consider breaking down")

        # Check for conflicting instructions
        if "don't" in prompt.lower() and "do" in prompt.lower():
            issues["major"].append("Potentially conflicting instructions")

        # Minor issues
        if prompt.endswith("..."):
            issues["minor"].append("Prompt appears incomplete (ends with ...)")

        if prompt.count("?") > 5:
            issues["minor"].append("Too many questions - may confuse the model")

        total_issues = len(issues["critical"]) + len(issues["major"]) + len(issues["minor"])

        return {
            "success": True,
            "issues": issues,
            "total_issues": total_issues,
            "has_critical": len(issues["critical"]) > 0,
            "has_major": len(issues["major"]) > 0
        }

    def shutdown(self) -> bool:
        """Cleanup plugin resources"""
        self._initialized = False
        self.validation_rules = {}
        self.quality_metrics = {}
        self.validation_history = []
        return True
