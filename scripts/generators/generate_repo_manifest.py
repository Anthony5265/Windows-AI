#!/usr/bin/env python3
"""Generate a structured manifest describing the repository layout.

The manifest groups files and directories into curated categories based on
``docs/structure/catalog_config.yaml``. Each category enumerates its members and
optionally expands directories into a nested tree limited by a configurable
depth. The resulting JSON can be used by documentation tooling or surfaced in
handbooks to give contributors a consistent view of the repository.

Usage:
    python scripts/generate_repo_manifest.py \
        --config docs/structure/catalog_config.yaml

The script validates that every top-level path (excluding those configured to
be ignored) is assigned to at least one category.
"""

from __future__ import annotations

import argparse
import datetime as dt
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List, Optional, Set

try:
    import yaml
except ModuleNotFoundError as exc:  # pragma: no cover - surfaced to the caller
    raise SystemExit(
        "PyYAML is required to generate the repository manifest. Install it via "
        "`pip install pyyaml` and re-run the script."
    ) from exc


@dataclass
class ConfigEntry:
    """Represents a catalog entry to include in the manifest."""

    path: Path
    description: str
    kind: str = "directory"
    max_depth: Optional[int] = None
    collapsed: bool = False


def _sort_key(path: Path) -> tuple[int, str]:
    """Sort directories before files and order alphabetically."""

    return (0 if path.is_dir() else 1, path.name.lower())


def _build_tree(
    target: Path,
    base: Path,
    depth: int,
    exclude: Set[str],
) -> Dict[str, Any]:
    """Create a nested dictionary describing ``target`` and its children."""

    node: Dict[str, Any] = {
        "name": target.name,
        "path": str(target.relative_to(base)),
        "type": "directory",
    }

    if depth <= 0:
        node["truncated"] = True
        node["counts"] = {"directories": 0, "files": 0}
        return node

    total_dirs = 0
    total_files = 0
    children: List[Dict[str, Any]] = []

    for child in sorted(target.iterdir(), key=_sort_key):
        if child.name in exclude:
            continue
        if child.is_dir():
            child_node = _build_tree(child, base, depth - 1, exclude)
            total_dirs += 1 + child_node["counts"]["directories"]
            total_files += child_node["counts"]["files"]
            children.append(child_node)
        else:
            total_files += 1
            children.append(
                {
                    "name": child.name,
                    "path": str(child.relative_to(base)),
                    "type": "file",
                }
            )

    node["children"] = children
    node["counts"] = {"directories": total_dirs, "files": total_files}
    return node


def _load_entries(category: Dict[str, Any], root: Path) -> List[ConfigEntry]:
    entries: List[ConfigEntry] = []
    for raw in category.get("entries", []):
        path = Path(raw["path"])
        description = raw.get("description", "")
        kind = raw.get("kind", "directory")
        max_depth = raw.get("max_depth")
        collapsed = raw.get("collapsed", False)

        entry_path = (root / path).resolve()
        if not entry_path.exists():
            raise FileNotFoundError(f"Configured path '{path}' does not exist")

        entries.append(
            ConfigEntry(
                path=entry_path,
                description=description,
                kind=kind,
                max_depth=max_depth,
                collapsed=collapsed,
            )
        )
    return entries


def _collect_top_level(root: Path) -> Dict[str, str]:
    """Return mapping of top-level names to kind (``file`` or ``directory``)."""

    result: Dict[str, str] = {}
    for child in root.iterdir():
        result[child.name] = "directory" if child.is_dir() else "file"
    return result


def _entry_summary(entry: ConfigEntry, root: Path, default_depth: int, exclude: Set[str]) -> Dict[str, Any]:
    """Build the manifest fragment for a single catalog entry."""

    relative_path = entry.path.relative_to(root)
    manifest_entry: Dict[str, Any] = {
        "path": str(relative_path),
        "kind": entry.kind,
        "description": entry.description,
    }

    if entry.kind == "directory":
        if entry.collapsed:
            manifest_entry["collapsed"] = True
        else:
            depth = entry.max_depth if entry.max_depth is not None else default_depth
            tree = _build_tree(entry.path, root, depth, exclude)
            manifest_entry["counts"] = tree["counts"]
            manifest_entry["tree"] = tree

    return manifest_entry


def main(argv: Optional[List[str]] = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--config",
        default="docs/structure/catalog_config.yaml",
        help="Path to the catalog configuration file.",
    )
    parser.add_argument(
        "--output",
        help="Override the output path defined in the configuration.",
    )
    parser.add_argument(
        "--pretty",
        action="store_true",
        help="Emit human-readable JSON (default is compact).",
    )
    args = parser.parse_args(argv)

    config_path = Path(args.config)
    if not config_path.exists():
        raise SystemExit(f"Configuration file '{config_path}' not found")

    with config_path.open("r", encoding="utf-8") as handle:
        config = yaml.safe_load(handle)

    global_cfg = config.get("global", {})
    root = Path(global_cfg.get("root", ".")).resolve()
    default_depth = int(global_cfg.get("default_depth", 2))
    exclude = set(global_cfg.get("exclude", []))

    all_top_level = _collect_top_level(root)
    excluded = sorted(name for name in all_top_level if name in exclude)
    top_level = {name: kind for name, kind in all_top_level.items() if name not in exclude}

    categories = config.get("categories", [])
    manifest_categories: List[Dict[str, Any]] = []
    covered_names: Set[str] = set()

    for category in categories:
        name = category.get("name", "Unnamed Category")
        description = category.get("description", "")
        entries_cfg = _load_entries(category, root)
        entries_manifest: List[Dict[str, Any]] = []

        for entry_cfg, raw in zip(entries_cfg, category.get("entries", [])):
            entry_manifest = _entry_summary(entry_cfg, root, default_depth, exclude)
            entries_manifest.append(entry_manifest)

            covered_names.add(entry_cfg.path.relative_to(root).parts[0])

        manifest_categories.append(
            {
                "name": name,
                "description": description,
                "entries": entries_manifest,
            }
        )

    unassigned = sorted(name for name in top_level if name not in covered_names)
    if unassigned:
        missing = ", ".join(unassigned)
        raise SystemExit(
            "The following top-level paths are not assigned to any category: "
            f"{missing}"
        )

    manifest: Dict[str, Any] = {
        "generated_at": dt.datetime.now(dt.timezone.utc).isoformat(timespec="seconds"),
        "root": str(root),
        "config": str(config_path.resolve()),
        "categories": manifest_categories,
        "coverage": {
            "assigned": sorted(covered_names),
            "excluded": excluded,
        },
    }

    output_path = Path(args.output) if args.output else Path(global_cfg.get("output", "manifest.json"))
    output_path.parent.mkdir(parents=True, exist_ok=True)

    with output_path.open("w", encoding="utf-8") as handle:
        json.dump(manifest, handle, indent=2 if args.pretty else None)
        handle.write("\n")

    print(f"Manifest written to {output_path}")
    return 0


if __name__ == "__main__":  # pragma: no cover - script entry point
    raise SystemExit(main())
