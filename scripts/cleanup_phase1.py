#!/usr/bin/env python3
"""
Phase 1 Cleanup: Remove Duplicates and Consolidate Roadmaps
"""

import os
import shutil
from pathlib import Path

def cleanup_phase_1():
    """Remove obvious duplicates and temporary files"""
    repo_root = Path.cwd()
    
    print("=" * 80)
    print("PHASE 1 CLEANUP: Removing Duplicates")
    print("=" * 80)
    
    actions = []
    
    # 1. Remove release backup directory (it's a duplicate)
    release_dir = repo_root / "release-20251105-223624"
    if release_dir.exists():
        actions.append(("Remove backup release directory", release_dir))
    
    # 2. Remove empty generated_code.txt files
    archive_extensions = repo_root / "archive" / "extension-generation" / "extensions_parallel"
    if archive_extensions.exists():
        empty_files = list(archive_extensions.glob("*/generated_code.txt"))
        for f in empty_files:
            if f.stat().st_size < 100:  # Empty or nearly empty
                actions.append(("Remove empty generated file", f))
    
    # 3. Remove duplicate .gitkeep files (keep only necessary ones)
    gitkeeps = list(repo_root.glob("**/.gitkeep"))
    necessary_dirs = {'config', 'logs', 'temp', 'cache'}
    for gitkeep in gitkeeps:
        parent_name = gitkeep.parent.name
        if parent_name not in necessary_dirs and gitkeep.parent != repo_root / "config":
            actions.append(("Remove unnecessary .gitkeep", gitkeep))
    
    # Display planned actions
    print(f"\n📋 Planned Actions: {len(actions)}")
    for i, (action, path) in enumerate(actions[:20], 1):
        rel_path = path.relative_to(repo_root)
        print(f"{i}. {action}: {rel_path}")
    
    if len(actions) > 20:
        print(f"... and {len(actions) - 20} more")
    
    # Confirm
    print(f"\n⚠️  This will remove/modify {len(actions)} items")
    response = input("Proceed? (yes/no): ")
    
    if response.lower() == 'yes':
        removed_count = 0
        for action, path in actions:
            try:
                if path.is_dir():
                    shutil.rmtree(path)
                else:
                    path.unlink()
                removed_count += 1
            except Exception as e:
                print(f"❌ Error with {path}: {e}")
        
        print(f"\n✅ Removed {removed_count} items")
    else:
        print("\n❌ Cleanup cancelled")

def consolidate_roadmaps():
    """Consolidate all roadmap files"""
    repo_root = Path.cwd()
    
    print("\n" + "=" * 80)
    print("ROADMAP CONSOLIDATION")
    print("=" * 80)
    
    # Keep COMPLETE_ROADMAP_TO_100.md as master
    master_roadmap = repo_root / "docs" / "roadmap-archive" / "COMPLETE_ROADMAP_TO_100.md"
    
    if not master_roadmap.exists():
        print("❌ Master roadmap not found!")
        return
    
    print(f"\n✅ Master Roadmap: {master_roadmap.name}")
    print(f"   Size: {master_roadmap.stat().st_size / 1024:.1f} KB")
    print(f"   Items: 3,330")
    
    # Create new unified ROADMAP.md pointing to master
    new_roadmap = repo_root / "docs" / "ROADMAP.md"
    
    content = f"""# Windows-AI Roadmap

**Official Roadmap Location:** [`docs/roadmap-archive/COMPLETE_ROADMAP_TO_100.md`](roadmap-archive/COMPLETE_ROADMAP_TO_100.md)

## Overview

The Windows-AI project has a comprehensive roadmap with **3,330 implementation items** across 3 phases:

- **Phase 1** ✅ COMPLETE (4 items) - Core infrastructure
- **Phase 2** 📋 IN PROGRESS (3,260 items) - All extensions across 19 categories  
- **Phase 3** 📋 PLANNED (43 items) - Final polish and installer

## Phase 2 Categories (3,260 items)

1. Core AI & Machine Learning (150+ items)
2. Windows OS Deep Integration (200+ items)
3. Web & Internet Integration (150+ items)
4. Developer Tools & IDEs (200+ items)
5. Data Science & Analytics (100+ items)
6. Smart Home & IoT (150+ items)
7. Gaming & Entertainment (100+ items)
8. Creative & Design Tools (100+ items)
9. Accessibility & Localization (80+ items)
10. Performance & Infrastructure (80+ items)
11. Mobile & Cross-Platform (80+ items)
12. Health & Wellness (60+ items)
13. Finance & Business (80+ items)
14. Emerging Technologies (100+ items)
15. Productivity (60+ items)
16. Social & Community (40+ items)
17. Education (50+ items)
18. Transportation (40+ items)
19. Industry Solutions (100+ items)

## Documentation

- **Master Roadmap:** [COMPLETE_ROADMAP_TO_100.md](roadmap-archive/COMPLETE_ROADMAP_TO_100.md)
- **Implementation Tracking:** [ROADMAP_IMPLEMENTATION.md](ROADMAP_IMPLEMENTATION.md)
- **Archive:** [roadmap-archive/](roadmap-archive/) - Historical roadmap versions

## Status Tracking

Current implementation status can be tracked via:
1. GitHub Issues
2. Project Boards
3. Automated scripts in `scripts/roadmap_tracker.py`

## Contributing

See [CONTRIBUTING.md](../CONTRIBUTING.md) for guidelines on implementing roadmap items.
"""
    
    # Backup old ROADMAP.md
    if new_roadmap.exists():
        backup = repo_root / "docs" / "roadmap-archive" / "OLD_ROADMAP.md"
        shutil.copy(new_roadmap, backup)
        print(f"\n📦 Backed up old roadmap to: {backup.name}")
    
    new_roadmap.write_text(content, encoding='utf-8')
    print(f"✅ Created new unified ROADMAP.md")
    
    print("\n" + "=" * 80)
    print("ROADMAP CONSOLIDATION COMPLETE")
    print("=" * 80)
    print("\nNext steps:")
    print("1. Review docs/ROADMAP.md")
    print("2. Archive or delete redundant roadmap files")
    print("3. Begin systematic implementation")

if __name__ == "__main__":
    cleanup_phase_1()
    consolidate_roadmaps()
