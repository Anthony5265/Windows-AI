"""
Chain of Thought Prompting Plugin
Generate and manage chain-of-thought prompts for step-by-step reasoning
"""

from typing import Dict, Any, Optional, List


class ChainOfThoughtPromptingPlugin:
    """Plugin for chain-of-thought prompt generation"""

    name = "chain_of_thought_prompting"
    version = "1.0.0"
    description = "Create effective chain-of-thought prompts for complex reasoning"
    author = "Windows AI Team"

    def __init__(self):
        self.cot_templates = {}
        self.problem_types = {}
        self._initialized = False

    def initialize(self, config: Optional[Dict[str, Any]] = None) -> bool:
        """Initialize the Chain of Thought Prompting plugin"""
        try:
            # Initialize default CoT templates
            self.cot_templates = {
                "basic": "{problem}\n\nLet's think step by step:",
                "explicit": "{problem}\n\nLet's solve this step-by-step:\nStep 1:",
                "numbered": "{problem}\n\nLet's break this down:\n1. First,\n2. Then,\n3. Finally,",
                "question_driven": "{problem}\n\nTo solve this, let's answer these questions:\nQ1: What do we know?\nQ2: What do we need to find?\nQ3: How can we get there?",
                "zero_shot": "{problem}\n\nLet's approach this systematically.",
                "few_shot": "{examples}\n\nNow let's solve:\n{problem}\n\nLet's think step by step:"
            }

            # Problem type specific templates
            self.problem_types = {
                "math": "{problem}\n\nLet's solve this step by step:\n1. Identify what we're looking for\n2. Set up the equation\n3. Solve\n4. Verify",
                "logic": "{problem}\n\nLet's reason through this:\n1. State the premises\n2. Apply logical rules\n3. Draw conclusions",
                "analysis": "{problem}\n\nLet's analyze this systematically:\n1. Break down the components\n2. Examine relationships\n3. Synthesize insights",
                "coding": "{problem}\n\nLet's plan the solution:\n1. Understand requirements\n2. Design approach\n3. Consider edge cases\n4. Implement"
            }

            self._initialized = True
            return True
        except Exception as e:
            print(f"Error initializing CoT Prompting plugin: {e}")
            return False

    def execute(self, action: str, params: Dict[str, Any]) -> Dict[str, Any]:
        """Execute a CoT Prompting action"""
        if not self._initialized:
            return {"success": False, "error": "Plugin not initialized"}

        try:
            if action == "generate_cot_prompt":
                return self._generate_cot_prompt(params)
            elif action == "add_reasoning_steps":
                return self._add_reasoning_steps(params)
            elif action == "create_few_shot_cot":
                return self._create_few_shot_cot(params)
            elif action == "decompose_problem":
                return self._decompose_problem(params)
            elif action == "add_verification_step":
                return self._add_verification_step(params)
            elif action == "create_self_consistency":
                return self._create_self_consistency(params)
            elif action == "analyze_reasoning_chain":
                return self._analyze_reasoning_chain(params)
            else:
                return {"success": False, "error": f"Unknown action: {action}"}
        except Exception as e:
            return {"success": False, "error": str(e)}

    def _generate_cot_prompt(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Generate a chain-of-thought prompt"""
        problem = params.get("problem", "")
        template_name = params.get("template", "basic")
        problem_type = params.get("problem_type", None)
        custom_steps = params.get("custom_steps", None)

        # Select template
        if problem_type and problem_type in self.problem_types:
            template = self.problem_types[problem_type]
        elif template_name in self.cot_templates:
            template = self.cot_templates[template_name]
        else:
            template = self.cot_templates["basic"]

        # Generate prompt
        prompt = template.format(problem=problem)

        # Add custom steps if provided
        if custom_steps:
            steps_text = "\n".join([f"Step {i+1}: {step}" for i, step in enumerate(custom_steps)])
            prompt += f"\n\n{steps_text}"

        return {
            "success": True,
            "prompt": prompt,
            "template_used": template_name,
            "problem_type": problem_type,
            "has_custom_steps": custom_steps is not None
        }

    def _add_reasoning_steps(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Add explicit reasoning steps to a prompt"""
        prompt = params.get("prompt", "")
        steps = params.get("steps", [])
        step_format = params.get("format", "numbered")  # numbered, bulleted, explicit

        if not steps:
            return {"success": False, "error": "No steps provided"}

        # Format steps
        if step_format == "numbered":
            formatted_steps = "\n".join([f"{i+1}. {step}" for i, step in enumerate(steps)])
        elif step_format == "bulleted":
            formatted_steps = "\n".join([f"- {step}" for step in steps])
        elif step_format == "explicit":
            formatted_steps = "\n".join([f"Step {i+1}: {step}" for i, step in enumerate(steps)])
        else:
            formatted_steps = "\n".join(steps)

        # Add to prompt
        enhanced_prompt = f"{prompt}\n\nReasoning steps:\n{formatted_steps}"

        return {
            "success": True,
            "original_prompt": prompt,
            "enhanced_prompt": enhanced_prompt,
            "num_steps": len(steps),
            "format": step_format
        }

    def _create_few_shot_cot(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Create few-shot CoT prompt with reasoning examples"""
        problem = params.get("problem", "")
        examples = params.get("examples", [])  # Each with: problem, reasoning, answer

        if not examples:
            return {"success": False, "error": "No examples provided"}

        # Format examples with reasoning
        formatted_examples = []
        for i, example in enumerate(examples):
            ex_text = f"Example {i+1}:\n"
            ex_text += f"Problem: {example.get('problem', '')}\n"
            ex_text += f"Reasoning: {example.get('reasoning', '')}\n"
            ex_text += f"Answer: {example.get('answer', '')}\n"
            formatted_examples.append(ex_text)

        examples_text = "\n\n".join(formatted_examples)

        # Create full prompt
        prompt = f"{examples_text}\n\nNow let's solve this problem:\n{problem}\n\nReasoning:"

        return {
            "success": True,
            "prompt": prompt,
            "num_examples": len(examples)
        }

    def _decompose_problem(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Decompose a problem into sub-problems"""
        problem = params.get("problem", "")
        num_subproblems = params.get("num_subproblems", 3)
        decomposition_strategy = params.get("strategy", "sequential")  # sequential, parallel, hierarchical

        # Create decomposition prompt
        if decomposition_strategy == "sequential":
            decomp_prompt = f"{problem}\n\nLet's break this into sequential steps:\n"
            for i in range(num_subproblems):
                decomp_prompt += f"Step {i+1}: [What needs to be done in this step?]\n"

        elif decomposition_strategy == "parallel":
            decomp_prompt = f"{problem}\n\nLet's identify independent sub-problems:\n"
            for i in range(num_subproblems):
                decomp_prompt += f"Sub-problem {i+1}: [What can be solved independently?]\n"

        elif decomposition_strategy == "hierarchical":
            decomp_prompt = f"{problem}\n\nLet's create a hierarchical breakdown:\n"
            decomp_prompt += "Main problem:\n"
            for i in range(num_subproblems):
                decomp_prompt += f"  Sub-problem {i+1}:\n"
                decomp_prompt += f"    - Component A\n"
                decomp_prompt += f"    - Component B\n"

        else:
            decomp_prompt = problem

        # Create sub-problem structure
        subproblems = []
        for i in range(num_subproblems):
            subproblems.append({
                "id": f"subproblem_{i+1}",
                "order": i + 1,
                "description": f"[Subproblem {i+1} to be defined]",
                "status": "pending"
            })

        return {
            "success": True,
            "original_problem": problem,
            "decomposition_prompt": decomp_prompt,
            "subproblems": subproblems,
            "strategy": decomposition_strategy
        }

    def _add_verification_step(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Add verification/checking step to CoT prompt"""
        prompt = params.get("prompt", "")
        verification_type = params.get("type", "general")  # general, numerical, logical

        verification_prompts = {
            "general": "\n\nVerification:\n- Does this answer make sense?\n- Did we address all parts of the problem?\n- Are there any contradictions?",
            "numerical": "\n\nVerification:\n- Let's check our calculations\n- Does the magnitude seem reasonable?\n- Can we verify using a different method?",
            "logical": "\n\nVerification:\n- Are our premises valid?\n- Does the conclusion follow logically?\n- Are there any logical fallacies?"
        }

        verification_text = verification_prompts.get(verification_type, verification_prompts["general"])
        enhanced_prompt = prompt + verification_text

        return {
            "success": True,
            "original_prompt": prompt,
            "enhanced_prompt": enhanced_prompt,
            "verification_type": verification_type
        }

    def _create_self_consistency(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Create multiple CoT prompts for self-consistency"""
        problem = params.get("problem", "")
        num_paths = params.get("num_paths", 3)
        diversity_prompts = params.get("diversity_prompts", [
            "Let's approach this from a different angle:",
            "Here's another way to think about it:",
            "Consider this alternative approach:"
        ])

        # Create multiple reasoning paths
        prompts = []

        # First path - standard CoT
        prompts.append({
            "path_id": 1,
            "prompt": f"{problem}\n\nLet's think step by step:",
            "approach": "standard"
        })

        # Additional diverse paths
        for i in range(1, min(num_paths, len(diversity_prompts) + 1)):
            diversity_prompt = diversity_prompts[i-1] if i-1 < len(diversity_prompts) else diversity_prompts[-1]
            prompts.append({
                "path_id": i + 1,
                "prompt": f"{problem}\n\n{diversity_prompt}",
                "approach": f"alternative_{i}"
            })

        # Aggregation prompt
        aggregation_prompt = (
            "Given the following reasoning paths:\n\n"
            "[Reasoning paths will be inserted here]\n\n"
            "What is the most consistent and reliable answer?"
        )

        return {
            "success": True,
            "problem": problem,
            "reasoning_paths": prompts,
            "num_paths": len(prompts),
            "aggregation_prompt": aggregation_prompt
        }

    def _analyze_reasoning_chain(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze the quality of a reasoning chain"""
        reasoning_chain = params.get("reasoning_chain", "")

        # Simple analysis (would be more sophisticated in production)
        analysis = {
            "has_steps": "step" in reasoning_chain.lower(),
            "has_conclusion": any(word in reasoning_chain.lower() for word in ["therefore", "thus", "so", "conclusion"]),
            "has_verification": any(word in reasoning_chain.lower() for word in ["check", "verify", "confirm"]),
            "num_steps": reasoning_chain.lower().count("step"),
            "length": len(reasoning_chain),
            "has_logical_connectors": any(word in reasoning_chain.lower() for word in ["because", "since", "if", "then"]),
            "quality_indicators": []
        }

        # Quality scoring
        quality_score = 0.0

        if analysis["has_steps"]:
            quality_score += 0.25
            analysis["quality_indicators"].append("Contains explicit steps")

        if analysis["has_conclusion"]:
            quality_score += 0.20
            analysis["quality_indicators"].append("Has clear conclusion")

        if analysis["has_verification"]:
            quality_score += 0.20
            analysis["quality_indicators"].append("Includes verification")

        if analysis["has_logical_connectors"]:
            quality_score += 0.15
            analysis["quality_indicators"].append("Uses logical connectors")

        if analysis["num_steps"] >= 3:
            quality_score += 0.20
            analysis["quality_indicators"].append("Multiple reasoning steps")

        analysis["quality_score"] = min(quality_score, 1.0)

        # Suggestions
        suggestions = []
        if not analysis["has_steps"]:
            suggestions.append("Add explicit step-by-step reasoning")
        if not analysis["has_conclusion"]:
            suggestions.append("Add a clear conclusion")
        if not analysis["has_verification"]:
            suggestions.append("Include verification of the answer")
        if analysis["num_steps"] < 3:
            suggestions.append("Break down into more detailed steps")

        analysis["suggestions"] = suggestions

        return {
            "success": True,
            "analysis": analysis,
            "reasoning_chain_length": len(reasoning_chain)
        }

    def shutdown(self) -> bool:
        """Cleanup plugin resources"""
        self._initialized = False
        self.cot_templates = {}
        self.problem_types = {}
        return True
