"""
Few-Shot Learning Plugin
Create and manage few-shot examples for improved LLM performance
"""

from typing import Dict, Any, Optional, List


class FewShotLearningPlugin:
    """Plugin for few-shot learning and example management"""

    name = "few_shot_learning"
    version = "1.0.0"
    description = "Manage few-shot examples and create effective prompts"
    author = "Windows AI Team"

    def __init__(self):
        self.example_sets = {}
        self.templates = {}
        self._initialized = False

    def initialize(self, config: Optional[Dict[str, Any]] = None) -> bool:
        """Initialize the Few-Shot Learning plugin"""
        try:
            # Initialize default templates
            self.templates = {
                "basic": "{examples}\n\n{task}",
                "instruction": "{instruction}\n\nExamples:\n{examples}\n\nNow:\n{task}",
                "chain_of_thought": "{examples}\n\nLet's solve this step by step:\n{task}",
                "labeled": "### Examples ###\n{examples}\n\n### Your Task ###\n{task}"
            }
            self._initialized = True
            return True
        except Exception as e:
            print(f"Error initializing Few-Shot Learning plugin: {e}")
            return False

    def execute(self, action: str, params: Dict[str, Any]) -> Dict[str, Any]:
        """Execute a Few-Shot Learning action"""
        if not self._initialized:
            return {"success": False, "error": "Plugin not initialized"}

        try:
            if action == "create_example_set":
                return self._create_example_set(params)
            elif action == "add_example":
                return self._add_example(params)
            elif action == "generate_prompt":
                return self._generate_prompt(params)
            elif action == "select_examples":
                return self._select_examples(params)
            elif action == "validate_examples":
                return self._validate_examples(params)
            elif action == "balance_examples":
                return self._balance_examples(params)
            elif action == "create_cot_examples":
                return self._create_cot_examples(params)
            else:
                return {"success": False, "error": f"Unknown action: {action}"}
        except Exception as e:
            return {"success": False, "error": str(e)}

    def _create_example_set(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Create a new example set"""
        set_id = params.get("set_id", f"set_{len(self.example_sets)}")
        task_description = params.get("task_description", "")
        example_type = params.get("type", "general")  # general, classification, generation, cot

        example_set = {
            "id": set_id,
            "task_description": task_description,
            "type": example_type,
            "examples": [],
            "metadata": {},
            "created_at": "now"
        }

        self.example_sets[set_id] = example_set

        return {
            "success": True,
            "example_set": example_set,
            "set_id": set_id
        }

    def _add_example(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Add an example to an example set"""
        set_id = params.get("set_id", "")
        input_text = params.get("input", "")
        output_text = params.get("output", "")
        reasoning = params.get("reasoning", None)  # For chain-of-thought
        metadata = params.get("metadata", {})

        if set_id not in self.example_sets:
            return {"success": False, "error": f"Example set {set_id} not found"}

        example = {
            "input": input_text,
            "output": output_text,
            "reasoning": reasoning,
            "metadata": metadata
        }

        self.example_sets[set_id]["examples"].append(example)

        return {
            "success": True,
            "example": example,
            "total_examples": len(self.example_sets[set_id]["examples"])
        }

    def _generate_prompt(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Generate a few-shot prompt from example set"""
        set_id = params.get("set_id", "")
        task = params.get("task", "")
        template_name = params.get("template", "basic")
        num_examples = params.get("num_examples", None)
        instruction = params.get("instruction", "")

        if set_id not in self.example_sets:
            return {"success": False, "error": f"Example set {set_id} not found"}

        example_set = self.example_sets[set_id]
        examples = example_set["examples"]

        # Select subset if specified
        if num_examples and num_examples < len(examples):
            examples = examples[:num_examples]

        # Format examples
        formatted_examples = self._format_examples(examples, example_set["type"])

        # Get template
        template = self.templates.get(template_name, self.templates["basic"])

        # Generate prompt
        prompt = template.format(
            examples=formatted_examples,
            task=task,
            instruction=instruction or example_set.get("task_description", "")
        )

        return {
            "success": True,
            "prompt": prompt,
            "num_examples_used": len(examples),
            "template": template_name,
            "example_type": example_set["type"]
        }

    def _format_examples(self, examples: List[Dict[str, Any]], example_type: str) -> str:
        """Format examples based on type"""
        formatted = []

        for i, example in enumerate(examples):
            if example_type == "cot":
                # Chain-of-thought format
                ex_str = f"Example {i+1}:\n"
                ex_str += f"Input: {example['input']}\n"
                if example.get("reasoning"):
                    ex_str += f"Reasoning: {example['reasoning']}\n"
                ex_str += f"Output: {example['output']}\n"
            elif example_type == "classification":
                # Classification format
                ex_str = f"Input: {example['input']}\nLabel: {example['output']}"
            elif example_type == "generation":
                # Generation format
                ex_str = f"Prompt: {example['input']}\nGenerated: {example['output']}"
            else:
                # General format
                ex_str = f"Input: {example['input']}\nOutput: {example['output']}"

            formatted.append(ex_str)

        return "\n\n".join(formatted)

    def _select_examples(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Intelligently select examples based on task"""
        set_id = params.get("set_id", "")
        task = params.get("task", "")
        num_examples = params.get("num_examples", 3)
        selection_strategy = params.get("strategy", "diverse")  # diverse, similar, random

        if set_id not in self.example_sets:
            return {"success": False, "error": f"Example set {set_id} not found"}

        example_set = self.example_sets[set_id]
        all_examples = example_set["examples"]

        if len(all_examples) <= num_examples:
            selected = all_examples
        else:
            if selection_strategy == "diverse":
                # Select diverse examples (simplified - would use embeddings)
                step = len(all_examples) // num_examples
                selected = [all_examples[i * step] for i in range(num_examples)]

            elif selection_strategy == "similar":
                # Select examples similar to task (simplified)
                # In real implementation, would use semantic similarity
                selected = all_examples[:num_examples]

            elif selection_strategy == "random":
                import random
                selected = random.sample(all_examples, num_examples)

            else:
                selected = all_examples[:num_examples]

        return {
            "success": True,
            "selected_examples": selected,
            "num_selected": len(selected),
            "strategy": selection_strategy,
            "total_available": len(all_examples)
        }

    def _validate_examples(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Validate example set quality"""
        set_id = params.get("set_id", "")

        if set_id not in self.example_sets:
            return {"success": False, "error": f"Example set {set_id} not found"}

        example_set = self.example_sets[set_id]
        examples = example_set["examples"]

        validation_results = {
            "num_examples": len(examples),
            "issues": [],
            "warnings": [],
            "quality_score": 0.0
        }

        # Check minimum number of examples
        if len(examples) < 2:
            validation_results["issues"].append("Too few examples (minimum 2 recommended)")
        elif len(examples) < 3:
            validation_results["warnings"].append("Only 2 examples - consider adding more")

        # Check for empty examples
        for i, example in enumerate(examples):
            if not example.get("input"):
                validation_results["issues"].append(f"Example {i}: Empty input")
            if not example.get("output"):
                validation_results["issues"].append(f"Example {i}: Empty output")

        # Check for diversity (simplified)
        unique_inputs = len(set([ex["input"] for ex in examples if ex.get("input")]))
        if unique_inputs < len(examples):
            validation_results["warnings"].append("Duplicate inputs detected")

        # Check example length consistency
        input_lengths = [len(str(ex.get("input", ""))) for ex in examples]
        if input_lengths:
            avg_length = sum(input_lengths) / len(input_lengths)
            for i, length in enumerate(input_lengths):
                if length > avg_length * 3:
                    validation_results["warnings"].append(f"Example {i}: Unusually long input")
                elif length < avg_length / 3 and length > 0:
                    validation_results["warnings"].append(f"Example {i}: Unusually short input")

        # Calculate quality score
        quality_score = 1.0
        quality_score -= len(validation_results["issues"]) * 0.2
        quality_score -= len(validation_results["warnings"]) * 0.1
        quality_score = max(quality_score, 0.0)

        validation_results["quality_score"] = quality_score
        validation_results["is_valid"] = len(validation_results["issues"]) == 0

        return {
            "success": True,
            "set_id": set_id,
            "validation": validation_results
        }

    def _balance_examples(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Balance examples across different classes or types"""
        set_id = params.get("set_id", "")
        label_field = params.get("label_field", "output")  # Which field contains the label
        max_per_class = params.get("max_per_class", None)

        if set_id not in self.example_sets:
            return {"success": False, "error": f"Example set {set_id} not found"}

        example_set = self.example_sets[set_id]
        examples = example_set["examples"]

        # Group by label
        label_groups = {}
        for example in examples:
            label = str(example.get(label_field, "unknown"))
            if label not in label_groups:
                label_groups[label] = []
            label_groups[label].append(example)

        # Balance
        balanced_examples = []
        for label, label_examples in label_groups.items():
            if max_per_class and len(label_examples) > max_per_class:
                balanced_examples.extend(label_examples[:max_per_class])
            else:
                balanced_examples.extend(label_examples)

        # Create new balanced set
        balanced_set_id = f"{set_id}_balanced"
        balanced_set = {
            "id": balanced_set_id,
            "task_description": example_set["task_description"],
            "type": example_set["type"],
            "examples": balanced_examples,
            "metadata": {"balanced_from": set_id},
            "created_at": "now"
        }

        self.example_sets[balanced_set_id] = balanced_set

        # Calculate distribution
        distribution = {label: len(examples) for label, examples in label_groups.items()}

        return {
            "success": True,
            "balanced_set_id": balanced_set_id,
            "original_count": len(examples),
            "balanced_count": len(balanced_examples),
            "label_distribution": distribution,
            "num_classes": len(label_groups)
        }

    def _create_cot_examples(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Create chain-of-thought examples from basic examples"""
        set_id = params.get("set_id", "")
        reasoning_template = params.get("reasoning_template", "Let's think step by step:")

        if set_id not in self.example_sets:
            return {"success": False, "error": f"Example set {set_id} not found"}

        example_set = self.example_sets[set_id]
        examples = example_set["examples"]

        # Create CoT versions
        cot_examples = []
        for example in examples:
            cot_example = {
                "input": example["input"],
                "output": example["output"],
                "reasoning": example.get("reasoning") or f"{reasoning_template} [Reasoning steps would be added here]",
                "metadata": {**example.get("metadata", {}), "converted_to_cot": True}
            }
            cot_examples.append(cot_example)

        # Create new CoT example set
        cot_set_id = f"{set_id}_cot"
        cot_set = {
            "id": cot_set_id,
            "task_description": example_set["task_description"],
            "type": "cot",
            "examples": cot_examples,
            "metadata": {"created_from": set_id},
            "created_at": "now"
        }

        self.example_sets[cot_set_id] = cot_set

        return {
            "success": True,
            "cot_set_id": cot_set_id,
            "num_examples": len(cot_examples),
            "original_set_id": set_id
        }

    def shutdown(self) -> bool:
        """Cleanup plugin resources"""
        self._initialized = False
        self.example_sets = {}
        self.templates = {}
        return True
