from __future__ import annotations

"""Tiny wrapper around :mod:`llama_cpp` for offline inference.

The module attempts to load a small GGUF/GPT model so the installer can offer
basic conversational abilities without requiring an internet connection.  The
model path can be overridden via ``load_model`` but defaults to a file named
``tiny.gguf`` next to this module.

All interactions are optional; if the model or dependency is missing the
functions gracefully fail and callers can fall back to rule based logic.
"""

from pathlib import Path
from typing import Iterator, Optional

try:  # pragma: no cover - optional dependency
    from llama_cpp import Llama  # type: ignore
except Exception:  # pragma: no cover - imported lazily
    Llama = None  # type: ignore

_MODEL: Optional["Llama"] = None


def load_model(model_path: str | None = None) -> bool:
    """Attempt to load a local GGUF model.

    Parameters
    ----------
    model_path:
        Optional path to a GGUF/GPT model.  If omitted, ``tiny.gguf`` next to
        this file is used.  Returns ``True`` if the model was loaded
        successfully, ``False`` otherwise.
    """

    global _MODEL
    if Llama is None:
        return False

    path = Path(model_path) if model_path else Path(__file__).with_name("tiny.gguf")
    if not path.exists():
        return False

    try:  # pragma: no cover - heavy init
        _MODEL = Llama(model_path=str(path), n_threads=1)  # type: ignore[arg-type]
    except Exception:
        _MODEL = None
    return _MODEL is not None


def answer_stream(prompt: str) -> Iterator[str]:
    """Yield response tokens from the local model for *prompt*.

    Raises ``RuntimeError`` if the model is unavailable.
    """

    if _MODEL is None:
        raise RuntimeError("model not loaded")

    try:  # pragma: no cover - streaming handled externally
        for chunk in _MODEL(prompt, stream=True, max_tokens=128):
            token = chunk["choices"][0]["text"]
            if token:
                yield token
    except Exception as exc:  # pragma: no cover - runtime errors
        raise RuntimeError(str(exc)) from exc
