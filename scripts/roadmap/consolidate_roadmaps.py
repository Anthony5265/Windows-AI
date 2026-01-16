#!/usr/bin/env python3
"""
Consolidate multiple roadmap/TODO markdown files into a single canonical master roadmap
and generate a status dashboard with completion counts.

Usage:
  python scripts/roadmap/consolidate_roadmaps.py

Outputs:
  - docs/master_plan/ROADMAP_MASTER.md
  - docs/status/ROADMAP_STATUS.md

This script scans the repository for markdown files whose names contain
'ROADMAP' or 'TODO', and extracts checkbox list items:
  - [ ] Item text
  - [x] Item text

It deduplicates items by normalized text and groups them under the last
preceding heading (## or ###) found in the source file. Each consolidated item
includes a list of sources where it was found.
"""
from __future__ import annotations
import os
import re
import sys
import json
from dataclasses import dataclass, field
import string
from typing import Dict, List, Tuple, Optional

RE_CHECKBOX = re.compile(r"^\s*[-*]\s*\[(?P<done>[ xX])\]\s*(?P<text>.+?)\s*$")
RE_HEADING = re.compile(r"^\s*(?P<hashes>#{1,6})\s+(?P<title>.+?)\s*$")

SCAN_DIRS = [
    "docs",
]
SCAN_FILES = [
    "TODO_MASTER.md",  # root
]

OUTPUT_MASTER = os.path.join("docs", "master_plan", "ROADMAP_MASTER.md")
OUTPUT_STATUS = os.path.join("docs", "status", "ROADMAP_STATUS.md")

@dataclass
class Item:
    text: str
    done: bool
    category: str
    sources: List[str] = field(default_factory=list)

    def key(self) -> str:
        """Normalized key for deduplication."""
        t = self.text.lower()
        # remove punctuation and collapse whitespace
        t = t.translate(str.maketrans({c: " " for c in string.punctuation}))
        t = re.sub(r"\s+", " ", t).strip()
        return t


def iter_markdown_items(path: str) -> List[Item]:
    items: List[Item] = []
    category = "General"
    try:
        with open(path, "r", encoding="utf-8", errors="ignore") as f:
            for line in f:
                m_h = RE_HEADING.match(line)
                if m_h:
                    hashes = m_h.group("hashes")
                    # Only use h2/h3 for category grouping to avoid overly granular h4+.
                    if len(hashes) in (2, 3):
                        category = m_h.group("title").strip()
                    continue
                m = RE_CHECKBOX.match(line)
                if m:
                    done = m.group("done").strip().lower() == "x"
                    text = m.group("text").strip()
                    items.append(Item(text=text, done=done, category=category, sources=[path]))
    except Exception as e:
        print(f"[warn] Failed to parse {path}: {e}")
    return items


def scan_sources() -> Tuple[List[str], Dict[str, List[Item]]]:
    sources: List[str] = []
    items_by_source: Dict[str, List[Item]] = {}

    # Explicit files
    for fname in SCAN_FILES:
        if os.path.exists(fname):
            sources.append(fname)
            items_by_source[fname] = iter_markdown_items(fname)

    # Walk docs/ for ROADMAP/TODO markdowns
    for root_dir in SCAN_DIRS:
        if not os.path.exists(root_dir):
            continue
        for root, _dirs, files in os.walk(root_dir):
            for fn in files:
                if not fn.lower().endswith(".md"):
                    continue
                if "roadmap" in fn.lower() or "todo" in fn.lower():
                    path = os.path.join(root, fn)
                    sources.append(path)
                    items_by_source[path] = iter_markdown_items(path)
    return sources, items_by_source


def consolidate(items_by_source: Dict[str, List[Item]]) -> Dict[str, List[Item]]:
    """Return items grouped by category with deduplication across sources."""
    by_key: Dict[str, Item] = {}
    for src, items in items_by_source.items():
        for it in items:
            key = it.key()
            if key in by_key:
                # Merge
                existing = by_key[key]
                # Consider done if any source marks it done
                existing.done = existing.done or it.done
                # Prefer the most specific category (keep first non-General)
                if existing.category == "General" and it.category != "General":
                    existing.category = it.category
                # Append source
                existing.sources.append(src)
            else:
                by_key[key] = Item(text=it.text, done=it.done, category=it.category, sources=list(it.sources))
    # Group by category
    grouped: Dict[str, List[Item]] = {}
    for it in by_key.values():
        grouped.setdefault(it.category, []).append(it)
    # sort items in each category: undone first, then alphabetically
    for cat, arr in grouped.items():
        arr.sort(key=lambda x: (x.done, x.text.lower()))
    return grouped


def write_master(grouped: Dict[str, List[Item]], sources: List[str]) -> None:
    os.makedirs(os.path.dirname(OUTPUT_MASTER), exist_ok=True)
    total = sum(len(v) for v in grouped.values())
    completed = sum(1 for v in grouped.values() for it in v if it.done)
    remaining = total - completed
    pct = (completed / total * 100.0) if total else 0.0

    lines: List[str] = []
    lines.append("# Canonical Master Roadmap")
    lines.append("")
    lines.append(f"- Total: {total}")
    lines.append(f"- Completed: {completed}")
    lines.append(f"- Remaining: {remaining}")
    lines.append(f"- Progress: {pct:.1f}%")
    lines.append("")
    lines.append("## Sources")
    for s in sorted(set(sources)):
        lines.append(f"- {s}")
    lines.append("")
    for cat in sorted(grouped.keys()):
        lines.append(f"## {cat}")
        for it in grouped[cat]:
            box = "[x]" if it.done else "[ ]"
            # include sources inline as footnote-style list
            srcs = ", ".join(sorted(set(it.sources)))
            lines.append(f"- {box} {it.text} \n  - Sources: {srcs}")
        lines.append("")
    with open(OUTPUT_MASTER, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))
    print(f"[ok] Wrote {OUTPUT_MASTER}")


def write_status(items_by_source: Dict[str, List[Item]], grouped: Dict[str, List[Item]]) -> None:
    os.makedirs(os.path.dirname(OUTPUT_STATUS), exist_ok=True)
    total = sum(len(v) for v in grouped.values())
    completed = sum(1 for v in grouped.values() for it in v if it.done)
    remaining = total - completed
    pct = (completed / total * 100.0) if total else 0.0

    lines: List[str] = []
    lines.append("# Roadmap Status Dashboard")
    lines.append("")
    lines.append("## Overall")
    lines.append(f"- Total: {total}")
    lines.append(f"- Completed: {completed}")
    lines.append(f"- Remaining: {remaining}")
    lines.append(f"- Progress: {pct:.1f}%")
    lines.append("")
    lines.append("## By Source")
    for src in sorted(items_by_source.keys()):
        arr = items_by_source[src]
        t = len(arr)
        c = sum(1 for it in arr if it.done)
        r = t - c
        p = (c / t * 100.0) if t else 0.0
        lines.append(f"- {src}")
        lines.append(f"  - Total: {t}")
        lines.append(f"  - Completed: {c}")
        lines.append(f"  - Remaining: {r}")
        lines.append(f"  - Progress: {p:.1f}%")
    lines.append("")
    with open(OUTPUT_STATUS, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))
    print(f"[ok] Wrote {OUTPUT_STATUS}")


def main() -> int:
    sources, items_by_source = scan_sources()
    grouped = consolidate(items_by_source)
    write_master(grouped, sources)
    write_status(items_by_source, grouped)
    return 0

if __name__ == "__main__":
    sys.exit(main())
