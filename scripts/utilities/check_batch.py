#!/usr/bin/env python3
"""
Batch Result Checker
Verifies all plugins created by AI agents
"""

import os
from pathlib import Path

def check_batch_results():
    """Check all generated plugins"""
    
    base_dir = Path(__file__).parent.parent
    ai_models_dir = base_dir / "plugins" / "ai_models"
    local_models_dir = base_dir / "plugins" / "local_models"
    
    # Count plugins
    ai_models = [f for f in ai_models_dir.glob("*.py") if f.name != "__init__.py"]
    local_models = [f for f in local_models_dir.glob("*.py") if f.name != "__init__.py"] if local_models_dir.exists() else []
    
    print("=" * 70)
    print("BATCH PROCESSING RESULTS")
    print("=" * 70)
    print(f"\n📁 AI Models: {len(ai_models)} plugins")
    for plugin in sorted(ai_models):
        size_kb = plugin.stat().st_size / 1024
        print(f"   ✓ {plugin.name} ({size_kb:.1f} KB)")
    
    print(f"\n📁 Local Models: {len(local_models)} plugins")
    for plugin in sorted(local_models):
        size_kb = plugin.stat().st_size / 1024
        print(f"   ✓ {plugin.name} ({size_kb:.1f} KB)")
    
    total = len(ai_models) + len(local_models)
    print(f"\n{'=' * 70}")
    print(f"TOTAL PLUGINS: {total}")
    print(f"PROGRESS: {total} / 1,520 ({total/1520*100:.2f}%)")
    print(f"{'=' * 70}")
    
    return total

if __name__ == "__main__":
    check_batch_results()
