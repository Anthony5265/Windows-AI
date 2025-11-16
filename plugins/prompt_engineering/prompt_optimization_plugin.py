"""
Prompt Optimization Plugin
Automatically optimize prompts for better LLM performance
"""

from typing import Dict, Any, Optional, List


class PromptOptimizationPlugin:
    """Plugin for prompt engineering and optimization"""

    name = "prompt_optimization"
    version = "1.0.0"
    description = "Optimize prompts for better LLM performance"
    author = "Windows AI Team"

    def __init__(self):
        self.templates = {}
        self.optimization_history = []
        self._initialized = False

    def initialize(self, config: Optional[Dict[str, Any]] = None) -> bool:
        """Initialize the Prompt Optimization plugin"""
        try:
            # Load default templates
            self.templates = {
                "zero_shot": "Task: {task}\n\nPlease provide a detailed response.",
                "few_shot": "Here are some examples:\n{examples}\n\nNow, {task}",
                "chain_of_thought": "{task}\n\nLet's think step by step:",
                "instruction": "You are {role}. {task}\n\nRequirements:\n{requirements}",
                "template": "{instruction}\n\nContext: {context}\n\nQuery: {query}"
            }
            self._initialized = True
            return True
        except Exception as e:
            print(f"Error initializing Prompt Optimization plugin: {e}")
            return False

    def execute(self, action: str, params: Dict[str, Any]) -> Dict[str, Any]:
        """Execute a Prompt Optimization action"""
        if not self._initialized:
            return {"success": False, "error": "Plugin not initialized"}

        try:
            if action == "optimize":
                return self._optimize(params)
            elif action == "apply_template":
                return self._apply_template(params)
            elif action == "add_context":
                return self._add_context(params)
            elif action == "add_constraints":
                return self._add_constraints(params)
            elif action == "add_examples":
                return self._add_examples(params)
            elif action == "analyze_prompt":
                return self._analyze_prompt(params)
            else:
                return {"success": False, "error": f"Unknown action: {action}"}
        except Exception as e:
            return {"success": False, "error": str(e)}

    def _optimize(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Optimize a prompt through various techniques"""
        original_prompt = params.get("prompt", "")
        goal = params.get("goal", "clarity")
        techniques = params.get("techniques", ["clarity", "specificity", "structure"])

        optimizations = []
        optimized_prompt = original_prompt

        for technique in techniques:
            if technique == "clarity":
                opt = self._improve_clarity(optimized_prompt)
                optimizations.append({"technique": "clarity", "change": opt["improvement"]})
                optimized_prompt = opt["optimized"]

            elif technique == "specificity":
                opt = self._add_specificity(optimized_prompt)
                optimizations.append({"technique": "specificity", "change": opt["improvement"]})
                optimized_prompt = opt["optimized"]

            elif technique == "structure":
                opt = self._improve_structure(optimized_prompt)
                optimizations.append({"technique": "structure", "change": opt["improvement"]})
                optimized_prompt = opt["optimized"]

            elif technique == "constraints":
                opt = self._add_output_constraints(optimized_prompt)
                optimizations.append({"technique": "constraints", "change": opt["improvement"]})
                optimized_prompt = opt["optimized"]

        result = {
            "original": original_prompt,
            "optimized": optimized_prompt,
            "optimizations": optimizations,
            "improvement_score": self._score_improvement(original_prompt, optimized_prompt)
        }

        self.optimization_history.append(result)

        return {
            "success": True,
            **result
        }

    def _improve_clarity(self, prompt: str) -> Dict[str, str]:
        """Improve prompt clarity"""
        improvements = []

        # Add explicit instruction
        if not any(word in prompt.lower() for word in ["please", "task:", "instruction:"]):
            prompt = f"Task: {prompt}"
            improvements.append("Added explicit task framing")

        # Add output format
        if "?" in prompt and "answer" not in prompt.lower():
            prompt += "\n\nProvide a clear and concise answer."
            improvements.append("Added output expectation")

        return {
            "optimized": prompt,
            "improvement": " | ".join(improvements) if improvements else "No clarity improvements needed"
        }

    def _add_specificity(self, prompt: str) -> Dict[str, str]:
        """Add specificity to prompt"""
        improvements = []

        # Add detail requirements
        if len(prompt) < 50:
            prompt += "\n\nPlease provide detailed explanation with examples."
            improvements.append("Added detail requirement")

        # Add format specification
        if "list" not in prompt.lower() and "explain" in prompt.lower():
            prompt += "\n\nFormat: Use numbered points for clarity."
            improvements.append("Added format specification")

        return {
            "optimized": prompt,
            "improvement": " | ".join(improvements) if improvements else "No specificity improvements needed"
        }

    def _improve_structure(self, prompt: str) -> Dict[str, str]:
        """Improve prompt structure"""
        improvements = []

        # Add sections
        if "\n\n" not in prompt:
            parts = prompt.split(".")
            if len(parts) > 2:
                prompt = f"Objective:\n{parts[0]}.\n\nDetails:\n{'. '.join(parts[1:])}"
                improvements.append("Added sectioned structure")

        # Add role context
        if "you are" not in prompt.lower():
            prompt = f"You are a helpful AI assistant.\n\n{prompt}"
            improvements.append("Added role context")

        return {
            "optimized": prompt,
            "improvement": " | ".join(improvements) if improvements else "Structure already good"
        }

    def _add_output_constraints(self, prompt: str) -> Dict[str, str]:
        """Add output format constraints"""
        improvements = []

        constraints = "\n\nOutput constraints:\n- Be concise but complete\n- Use clear language\n- Provide evidence for claims"

        if "constraint" not in prompt.lower() and "requirement" not in prompt.lower():
            prompt += constraints
            improvements.append("Added output constraints")

        return {
            "optimized": prompt,
            "improvement": " | ".join(improvements) if improvements else "Constraints present"
        }

    def _score_improvement(self, original: str, optimized: str) -> float:
        """Score the improvement"""
        # Simple scoring based on length and structure
        original_score = len(original) * 0.001
        optimized_score = len(optimized) * 0.001

        # Bonus for structure
        if "\n\n" in optimized:
            optimized_score += 0.2
        if ":" in optimized:
            optimized_score += 0.1

        improvement = min((optimized_score - original_score) / original_score if original_score > 0 else 0, 1.0)
        return max(improvement, 0)

    def _apply_template(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Apply a prompt template"""
        template_name = params.get("template", "zero_shot")
        variables = params.get("variables", {})

        if template_name not in self.templates:
            return {"success": False, "error": f"Template {template_name} not found"}

        template = self.templates[template_name]

        # Fill in variables
        try:
            prompt = template.format(**variables)
        except KeyError as e:
            return {"success": False, "error": f"Missing variable: {e}"}

        return {
            "success": True,
            "template": template_name,
            "prompt": prompt,
            "variables_used": list(variables.keys())
        }

    def _add_context(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Add context to prompt"""
        prompt = params.get("prompt", "")
        context = params.get("context", "")

        enhanced = f"Context:\n{context}\n\n{prompt}"

        return {
            "success": True,
            "original": prompt,
            "enhanced": enhanced
        }

    def _add_constraints(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Add specific constraints to prompt"""
        prompt = params.get("prompt", "")
        constraints = params.get("constraints", [])

        if not constraints:
            return {"success": True, "prompt": prompt}

        constraint_text = "\n\nConstraints:\n" + "\n".join(f"- {c}" for c in constraints)
        enhanced = prompt + constraint_text

        return {
            "success": True,
            "original": prompt,
            "enhanced": enhanced,
            "constraints_added": len(constraints)
        }

    def _add_examples(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Add few-shot examples to prompt"""
        prompt = params.get("prompt", "")
        examples = params.get("examples", [])

        if not examples:
            return {"success": True, "prompt": prompt}

        example_text = "Examples:\n\n"
        for i, example in enumerate(examples):
            input_text = example.get("input", "")
            output_text = example.get("output", "")
            example_text += f"Example {i+1}:\nInput: {input_text}\nOutput: {output_text}\n\n"

        enhanced = example_text + "Now, your task:\n" + prompt

        return {
            "success": True,
            "original": prompt,
            "enhanced": enhanced,
            "examples_added": len(examples)
        }

    def _analyze_prompt(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze a prompt for quality"""
        prompt = params.get("prompt", "")

        analysis = {
            "length": len(prompt),
            "has_clear_task": any(word in prompt.lower() for word in ["task:", "please", "explain", "describe"]),
            "has_structure": "\n" in prompt,
            "has_examples": "example" in prompt.lower(),
            "has_constraints": any(word in prompt.lower() for word in ["constraint", "requirement", "must"]),
            "has_context": "context" in prompt.lower(),
            "clarity_score": 0.0,
            "completeness_score": 0.0,
            "suggestions": []
        }

        # Calculate scores
        score = 0
        if analysis["has_clear_task"]:
            score += 0.25
        if analysis["has_structure"]:
            score += 0.20
        if analysis["has_constraints"]:
            score += 0.20
        if analysis["has_context"]:
            score += 0.15
        if analysis["has_examples"]:
            score += 0.20

        analysis["clarity_score"] = score

        # Generate suggestions
        if not analysis["has_clear_task"]:
            analysis["suggestions"].append("Add explicit task instruction")
        if not analysis["has_structure"]:
            analysis["suggestions"].append("Organize with sections")
        if not analysis["has_constraints"]:
            analysis["suggestions"].append("Specify output constraints")
        if prompt and len(prompt) < 30:
            analysis["suggestions"].append("Add more detail and context")

        analysis["completeness_score"] = 1.0 - (len(analysis["suggestions"]) * 0.2)

        return {
            "success": True,
            "prompt": prompt,
            "analysis": analysis
        }

    def shutdown(self) -> bool:
        """Cleanup plugin resources"""
        self._initialized = False
        self.optimization_history = []
        return True
