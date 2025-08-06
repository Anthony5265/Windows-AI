"""Utilities for natural language processing tasks.

Each function serves as a placeholder for routing NLP-related operations through
local models or remote APIs.
"""

from __future__ import annotations
from typing import Any, Dict, List


def input_processor(raw_text: str) -> List[str]:
    """Preprocess ``raw_text`` before it is passed to models or APIs.

    The processor performs minimal normalization and tokenization.  For the
    purposes of this project we simply lowercase the text and split on
    whitespace, returning a list of tokens that downstream components can use to
    decide whether to route to local models or remote APIs.
    """

    # Normalize by trimming whitespace and converting to lowercase
    normalized = raw_text.strip().lower()
    # Tokenize using a naïve whitespace split.  Real implementations would use a
    # dedicated tokenizer but this is sufficient for demonstrating flow through
    # the pipeline.
    tokens = normalized.split()
    return tokens


def task_planner(processed_text: List[str]) -> Dict[str, Any]:
    """Plan the NLP task pipeline based on ``processed_text``.

    The planner creates a simple execution plan describing whether the tokens
    should be handled by a local model or dispatched to a remote service.  In
    this stub implementation we use the number of tokens as a heuristic: short
    inputs are processed locally while longer inputs are sent to a remote API.

    Returns a mapping with the key ``"plan"`` for compatibility with other
    components in the repository.
    """

    if len(processed_text) <= 1:
        # For very small inputs keep behaviour compatible with existing tests
        # and return an empty plan.  This mirrors the previous stub behaviour
        # used throughout the repository.
        return {"plan": []}

    mode = "local" if len(processed_text) <= 5 else "remote"
    plan = {
        "plan": [
            {
                "type": mode,
                "tokens": processed_text,
            }
        ]
    }
    return plan


def executor(plan: Dict[str, Any]) -> Dict[str, Any]:
    """Execute the planned NLP tasks.

    For demonstration we do not call actual models or remote services.  Instead
    the executor mirrors the planned ``type`` and returns a string indicating
    whether the processing was local or remote along with the original tokens.
    """

    results: List[str] = []
    for task in plan.get("plan", []):
        tokens = task.get("tokens", [])
        if task.get("type") == "local":
            results.append("LOCAL:" + " ".join(tokens))
        else:
            results.append("REMOTE:" + " ".join(tokens))
    return {"results": results}


def result_aggregator(results: Dict[str, Any]) -> Dict[str, Any]:
    """Combine outputs from executed NLP tasks.

    Aggregated results should unify responses from local models and APIs into a
    single structured output.
    """

    return results
