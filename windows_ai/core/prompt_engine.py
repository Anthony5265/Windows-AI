"""
Prompt Engineering Engine — Template management, chain-of-thought, few-shot construction,
prompt optimization, and structured output formatting.
"""
import logging
import re
import json
import uuid
from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional, Callable, Tuple
from enum import Enum

logger = logging.getLogger(__name__)


class PromptStrategy(Enum):
    ZERO_SHOT = "zero_shot"
    FEW_SHOT = "few_shot"
    CHAIN_OF_THOUGHT = "chain_of_thought"
    TREE_OF_THOUGHT = "tree_of_thought"
    REACT = "react"
    SELF_CONSISTENCY = "self_consistency"


class OutputFormat(Enum):
    TEXT = "text"
    JSON = "json"
    MARKDOWN = "markdown"
    CODE = "code"
    LIST = "list"
    TABLE = "table"


@dataclass
class PromptTemplate:
    template_id: str
    name: str
    template: str
    variables: List[str]
    strategy: PromptStrategy = PromptStrategy.ZERO_SHOT
    output_format: OutputFormat = OutputFormat.TEXT
    system_prompt: str = ""
    examples: List[Dict[str, str]] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)

    def render(self, **kwargs) -> str:
        result = self.template
        for var in self.variables:
            placeholder = "{" + var + "}"
            value = kwargs.get(var, "")
            result = result.replace(placeholder, str(value))
        return result

    def validate(self) -> Tuple[bool, List[str]]:
        errors = []
        found_vars = re.findall(r"\{(\w+)\}", self.template)
        for var in self.variables:
            if var not in found_vars:
                errors.append(f"Variable '{var}' not found in template")
        for var in found_vars:
            if var not in self.variables:
                errors.append(f"Template uses '{var}' but it's not in variables list")
        return len(errors) == 0, errors


@dataclass
class PromptChain:
    chain_id: str
    name: str
    steps: List[PromptTemplate]
    context: Dict[str, Any] = field(default_factory=dict)


@dataclass
class FewShotExample:
    input_text: str
    output_text: str
    reasoning: str = ""
    score: float = 1.0


class PromptOptimizer:
    """Optimizes prompts based on feedback and scoring."""

    def __init__(self):
        self._prompt_scores: Dict[str, List[float]] = {}
        self._variants: Dict[str, List[PromptTemplate]] = {}

    def add_score(self, template_id: str, score: float):
        self._prompt_scores.setdefault(template_id, []).append(score)

    def get_average_score(self, template_id: str) -> float:
        scores = self._prompt_scores.get(template_id, [])
        return sum(scores) / len(scores) if scores else 0.0

    def suggest_improvements(self, template: PromptTemplate) -> List[str]:
        suggestions = []
        if not template.system_prompt:
            suggestions.append("Add a system prompt for better context setting")
        if template.strategy == PromptStrategy.ZERO_SHOT and not template.examples:
            suggestions.append("Consider adding few-shot examples for better accuracy")
        if len(template.template) < 50:
            suggestions.append("Template seems short — add more context and instructions")
        if "{output_format}" not in template.template and template.output_format != OutputFormat.TEXT:
            suggestions.append("Add explicit output format instructions in the template")
        if "step by step" not in template.template.lower() and template.strategy == PromptStrategy.CHAIN_OF_THOUGHT:
            suggestions.append("Add 'step by step' instruction for chain-of-thought prompting")
        return suggestions

    def create_variant(self, template: PromptTemplate, modification: str) -> PromptTemplate:
        variant = PromptTemplate(
            template_id=str(uuid.uuid4()),
            name=f"{template.name}_variant",
            template=template.template,
            variables=list(template.variables),
            strategy=template.strategy,
            output_format=template.output_format,
            system_prompt=template.system_prompt,
            examples=list(template.examples),
            metadata={**template.metadata, "parent_id": template.template_id, "modification": modification}
        )
        if modification == "add_cot":
            variant.template += "\n\nLet's think about this step by step:"
            variant.strategy = PromptStrategy.CHAIN_OF_THOUGHT
        elif modification == "add_format":
            variant.template += f"\n\nPlease format your response as {variant.output_format.value}."
        elif modification == "simplify":
            variant.template = re.sub(r'\s+', ' ', variant.template).strip()
        elif modification == "elaborate":
            variant.template = f"I need a detailed and thorough response.\n\n{variant.template}\n\nBe comprehensive and specific."
        return variant


class FewShotManager:
    """Manages few-shot examples with selection strategies."""

    def __init__(self):
        self._examples: Dict[str, List[FewShotExample]] = {}

    def add_example(self, category: str, example: FewShotExample):
        self._examples.setdefault(category, []).append(example)

    def get_examples(self, category: str, n: int = 3, strategy: str = "top_scored") -> List[FewShotExample]:
        examples = self._examples.get(category, [])
        if not examples:
            return []
        if strategy == "top_scored":
            sorted_ex = sorted(examples, key=lambda x: x.score, reverse=True)
            return sorted_ex[:n]
        elif strategy == "diverse":
            # Select diverse examples by maximizing text dissimilarity
            if len(examples) <= n:
                return examples
            selected = [examples[0]]
            remaining = examples[1:]
            while len(selected) < n and remaining:
                max_min_dist = -1
                best_idx = 0
                for i, ex in enumerate(remaining):
                    min_dist = min(self._text_distance(ex.input_text, s.input_text) for s in selected)
                    if min_dist > max_min_dist:
                        max_min_dist = min_dist
                        best_idx = i
                selected.append(remaining.pop(best_idx))
            return selected
        else:  # random
            import random
            return random.sample(examples, min(n, len(examples)))

    def _text_distance(self, a: str, b: str) -> float:
        words_a = set(a.lower().split())
        words_b = set(b.lower().split())
        union = words_a | words_b
        if not union:
            return 0
        return 1 - len(words_a & words_b) / len(union)

    def format_examples(self, examples: List[FewShotExample], include_reasoning: bool = False) -> str:
        parts = []
        for i, ex in enumerate(examples, 1):
            part = f"Example {i}:\nInput: {ex.input_text}\n"
            if include_reasoning and ex.reasoning:
                part += f"Reasoning: {ex.reasoning}\n"
            part += f"Output: {ex.output_text}"
            parts.append(part)
        return "\n\n".join(parts)


class PromptEngine:
    """Main prompt engineering engine."""

    def __init__(self):
        self._templates: Dict[str, PromptTemplate] = {}
        self._chains: Dict[str, PromptChain] = {}
        self.optimizer = PromptOptimizer()
        self.few_shot_manager = FewShotManager()
        self._output_parsers: Dict[OutputFormat, Callable] = {
            OutputFormat.JSON: self._parse_json,
            OutputFormat.LIST: self._parse_list,
            OutputFormat.TABLE: self._parse_table,
        }
        logger.info("PromptEngine initialized")

    def register_template(self, template: PromptTemplate):
        self._templates[template.template_id] = template
        logger.info(f"Template registered: {template.name} ({template.template_id})")

    def get_template(self, template_id: str) -> Optional[PromptTemplate]:
        return self._templates.get(template_id)

    def create_template(self, name: str, template: str, variables: List[str],
                        strategy: PromptStrategy = PromptStrategy.ZERO_SHOT,
                        output_format: OutputFormat = OutputFormat.TEXT,
                        system_prompt: str = "") -> PromptTemplate:
        tmpl = PromptTemplate(
            template_id=str(uuid.uuid4()), name=name, template=template,
            variables=variables, strategy=strategy, output_format=output_format,
            system_prompt=system_prompt
        )
        self.register_template(tmpl)
        return tmpl

    def build_prompt(self, template_id: str, few_shot_category: str = None,
                     n_examples: int = 3, **kwargs) -> str:
        template = self._templates.get(template_id)
        if not template:
            raise ValueError(f"Template not found: {template_id}")

        parts = []

        # System prompt
        if template.system_prompt:
            parts.append(f"System: {template.system_prompt}")

        # Few-shot examples
        if few_shot_category or template.examples:
            if few_shot_category:
                examples = self.few_shot_manager.get_examples(few_shot_category, n_examples)
                include_reasoning = template.strategy == PromptStrategy.CHAIN_OF_THOUGHT
                parts.append(self.few_shot_manager.format_examples(examples, include_reasoning))
            elif template.examples:
                for ex in template.examples[:n_examples]:
                    parts.append(f"Input: {ex.get('input', '')}\nOutput: {ex.get('output', '')}")

        # Main prompt
        rendered = template.render(**kwargs)
        parts.append(rendered)

        # Chain-of-thought instruction
        if template.strategy == PromptStrategy.CHAIN_OF_THOUGHT:
            if "step by step" not in rendered.lower():
                parts.append("Let's work through this step by step:")

        # Output format instruction
        if template.output_format == OutputFormat.JSON:
            parts.append("Please respond with valid JSON only.")
        elif template.output_format == OutputFormat.MARKDOWN:
            parts.append("Please format your response in Markdown.")
        elif template.output_format == OutputFormat.CODE:
            lang = kwargs.get("language", "python")
            parts.append(f"Please respond with {lang} code only.")
        elif template.output_format == OutputFormat.LIST:
            parts.append("Please respond with a numbered list.")

        return "\n\n".join(parts)

    def parse_output(self, output: str, format_type: OutputFormat) -> Any:
        parser = self._output_parsers.get(format_type)
        if parser:
            return parser(output)
        return output

    def _parse_json(self, text: str) -> Any:
        # Try to extract JSON from text
        json_match = re.search(r'[{\[].*[}\]]', text, re.DOTALL)
        if json_match:
            try:
                return json.loads(json_match.group())
            except json.JSONDecodeError:
                pass
        return {"raw": text}

    def _parse_list(self, text: str) -> List[str]:
        items = re.findall(r'^\s*(?:\d+[.)]|[-*])\s*(.+)$', text, re.MULTILINE)
        if items:
            return items
        return [line.strip() for line in text.split("\n") if line.strip()]

    def _parse_table(self, text: str) -> List[Dict[str, str]]:
        lines = [l.strip() for l in text.split("\n") if "|" in l]
        if len(lines) < 2:
            return []
        headers = [h.strip() for h in lines[0].split("|") if h.strip()]
        rows = []
        for line in lines[2:]:
            cells = [c.strip() for c in line.split("|") if c.strip()]
            if len(cells) == len(headers):
                rows.append(dict(zip(headers, cells)))
        return rows

    def create_react_prompt(self, task: str, tools: List[Dict[str, str]], context: str = "") -> str:
        tool_descriptions = "\n".join(f"- {t['name']}: {t['description']}" for t in tools)
        return f"""You are an AI assistant that can use tools to solve tasks.

Available tools:
{tool_descriptions}

To use a tool, respond with:
Thought: [your reasoning]
Action: [tool_name]
Action Input: [input to the tool]

When you have the final answer:
Thought: I now have the answer.
Final Answer: [your answer]

{f"Context: {context}" if context else ""}

Task: {task}

Thought:"""

    def create_chain(self, name: str, steps: List[PromptTemplate]) -> PromptChain:
        chain = PromptChain(chain_id=str(uuid.uuid4()), name=name, steps=steps)
        self._chains[chain.chain_id] = chain
        return chain

    def list_templates(self) -> List[Dict[str, Any]]:
        return [
            {"id": t.template_id, "name": t.name, "strategy": t.strategy.value, "variables": t.variables}
            for t in self._templates.values()
        ]


# Global instance
_engine: Optional[PromptEngine] = None

def get_prompt_engine() -> PromptEngine:
    global _engine
    if _engine is None:
        _engine = PromptEngine()
    return _engine
