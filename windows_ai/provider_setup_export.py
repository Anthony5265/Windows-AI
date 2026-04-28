"""Utilities for exporting Windows AI provider setup data.

This module gives the installer, GUI bootstrap layer, and support tooling a
single backend-native way to materialize provider discovery data as JSON. It is
intended to be lightweight and safe to run on demand:

- provider definitions
- current provider detections
- hardware-aware Ollama recommendations
- normalized target catalog
- installer actions

It can be imported as a library or executed as a small CLI:

    python -m windows_ai.provider_setup_export --output provider-setup.json
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any, Dict, Optional, Sequence

from windows_ai.provider_cli_registry import provider_cli_registry


def build_provider_setup_snapshot(
    *,
    catalog_only: bool = False,
    include_status_wrapper: bool = True,
) -> Dict[str, Any]:
    """Build the current provider setup payload.

    When ``catalog_only`` is true, this returns only the normalized target
    catalog. Otherwise it returns the full setup plan emitted by the provider
    registry.
    """

    payload = (
        provider_cli_registry.get_target_catalog()
        if catalog_only
        else provider_cli_registry.get_setup_plan()
    )

    if not include_status_wrapper:
        return payload

    return {
        "status": "success",
        **payload,
    }


def write_provider_setup_snapshot(
    output_path: str | Path,
    *,
    catalog_only: bool = False,
    compact: bool = False,
) -> Path:
    """Write the current provider setup payload to disk as JSON."""

    resolved_path = Path(output_path).expanduser().resolve()
    resolved_path.parent.mkdir(parents=True, exist_ok=True)

    payload = build_provider_setup_snapshot(
        catalog_only=catalog_only,
        include_status_wrapper=True,
    )

    json_kwargs = {"ensure_ascii": False}
    if compact:
        serialized = json.dumps(payload, separators=(",", ":"), **json_kwargs)
    else:
        serialized = json.dumps(payload, indent=2, **json_kwargs)

    resolved_path.write_text(serialized + "\n", encoding="utf-8")
    return resolved_path


def _build_argument_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Export Windows AI provider setup data as JSON.",
    )
    parser.add_argument(
        "--output",
        type=str,
        default=None,
        help="Optional file path to write. If omitted, JSON is printed to stdout.",
    )
    parser.add_argument(
        "--catalog-only",
        action="store_true",
        help="Export only the normalized provider target catalog.",
    )
    parser.add_argument(
        "--compact",
        action="store_true",
        help="Emit compact JSON instead of pretty-printed JSON.",
    )
    return parser


def main(argv: Optional[Sequence[str]] = None) -> int:
    parser = _build_argument_parser()
    args = parser.parse_args(list(argv) if argv is not None else None)

    if args.output:
        written_path = write_provider_setup_snapshot(
            args.output,
            catalog_only=args.catalog_only,
            compact=args.compact,
        )
        print(str(written_path))
        return 0

    payload = build_provider_setup_snapshot(
        catalog_only=args.catalog_only,
        include_status_wrapper=True,
    )
    json_kwargs = {"ensure_ascii": False}
    if args.compact:
        print(json.dumps(payload, separators=(",", ":"), **json_kwargs))
    else:
        print(json.dumps(payload, indent=2, **json_kwargs))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
