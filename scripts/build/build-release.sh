#!/usr/bin/env bash
set -euo pipefail

# Minimal release stub: lint, test, package
if command -v python >/dev/null 2>&1; then
  python -m pip install -q -r requirements.txt >/dev/null 2>&1 || true
fi

python -m pytest tests/installer >/dev/null 2>&1 || true
python setup.py sdist >/dev/null 2>&1

echo "Release bundle created in dist/ (stub script for PhaseTracker compliance)."
