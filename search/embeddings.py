from __future__ import annotations

from typing import Set


def embed(text: str) -> Set[str]:
    """Very small token-based embedding.

    The function lowercases the text and splits on whitespace, returning a
    set of tokens that can be used for similarity search."""

    return set(text.lower().split())
