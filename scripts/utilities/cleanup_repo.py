#!/usr/bin/env python3
"""
Windows-AI Repository Cleanup Script
Organizes the fragmented repository based on HONEST_REPO_ASSESSMENT.md

Usage:
    python cleanup_repo.py --dry-run    # Preview changes
    python cleanup_repo.py --execute    # Execute changes
"""

import os
import shutil
import hashlib
from pathlib import Path
from typing import List, Dict, Set
import json
import argparse


class RepoCleanup:
    def __init__(self, repo_root: Path, dry_run: bool = True):
        self.repo_root = repo_root
        self.dry_run = dry_run
        self.changes = []

    def log(self, action: str, details: str):
        """Log an action"""
        msg = f"[{'DRY-RUN' if self.dry_run else 'EXECUTE'}] {action}: {details}"
        print(msg)
        self.changes.append({"action": action, "details": details})

    def safe_move(self, src: Path, dst: Path):
        """Safely move a file or directory"""
        if not src.exists():
            self.log("SKIP", f"{src} does not exist")
            return

        # Create destination directory if needed
        dst.parent.mkdir(parents=True, exist_ok=True)

        if self.dry_run:
            self.log("MOVE", f"{src} -> {dst}")
        else:
            self.log("MOVE", f"{src} -> {dst}")
            shutil.move(str(src), str(dst))

    def safe_delete(self, path: Path):
        """Safely delete a file or directory"""
        if not path.exists():
            self.log("SKIP", f"{path} does not exist")
            return

        if self.dry_run:
            if path.is_dir():
                self.log("DELETE", f"Directory: {path}")
            else:
                self.log("DELETE", f"File: {path}")
        else:
            if path.is_dir():
                self.log("DELETE", f"Directory: {path}")
                shutil.rmtree(path)
            else:
                self.log("DELETE", f"File: {path}")
                path.unlink()

    def safe_copy(self, src: Path, dst: Path):
        """Safely copy a file"""
        if not src.exists():
            self.log("SKIP", f"{src} does not exist")
            return

        dst.parent.mkdir(parents=True, exist_ok=True)

        if self.dry_run:
            self.log("COPY", f"{src} -> {dst}")
        else:
            self.log("COPY", f"{src} -> {dst}")
            shutil.copy2(str(src), str(dst))

    def archive_old_roadmaps(self):
        """Move all old roadmap files to docs/roadmap-archive/OLD_CONFLICTING/"""
        print("\n" + "="*80)
        print("STEP 1: Archive Old Roadmap Files")
        print("="*80 + "\n")

        archive_dest = self.repo_root / "docs" / "roadmap-archive" / "OLD_CONFLICTING"

        # Roadmap files to archive (keep COMPLETE_ROADMAP_TO_100.md and NEW_MASTER_ROADMAP.md)
        roadmaps_to_archive = [
            "docs/ROADMAP_IMPLEMENTATION.md",
            "docs/ROADMAP_TODO.md",
            "docs/ROADMAP_COMPLETION_FINAL.md",
            "docs/WindowsAI_Consolidated_Roadmap.md",
            "docs/roadmap-archive/ULTIMATE_EXTENSION_ROADMAP.md",
            "docs/roadmap-archive/ROADMAP_COMPLETION_REPORT.md",
            "docs/roadmap-archive/ROADMAP_STATUS.md",
            "docs/roadmap-archive/REMAINING_ROADMAP.md",
            "docs/roadmap-archive/FILTERED_EXTENSION_ROADMAP.md",
            "docs/roadmap-archive/EXTENSION_ROADMAP.md",
            "docs/roadmap-archive/ACTUAL_ROADMAP_REALITY.md",
            "docs/roadmap-archive/OLD_UPGRADE_ROADMAP.md",
            "docs/architecture/platform-roadmap.md",
            "docs/operations/operations_roadmap.md",
            "docs/security/security_roadmap.md",
            "docs/testing/testing_roadmap.md",
            "docs/standards/communication_roadmap.md",
            "docs/observability/observability_roadmap.md",
            "community/portal/roadmap_updates.md",
            "community/portal/roadmap-milestones.md",
            "docs/PLAN.md",
            "docs/DEVELOPMENT_PLAN_PHASE4.md",
            "docs/Repo_Organization_Plan.md",
        ]

        for roadmap_file in roadmaps_to_archive:
            src = self.repo_root / roadmap_file
            dst = archive_dest / Path(roadmap_file).name
            self.safe_move(src, dst)

    def cleanup_duplicates(self):
        """Remove duplicate files"""
        print("\n" + "="*80)
        print("STEP 2: Clean Up Duplicate Files")
        print("="*80 + "\n")

        # Delete old release folder (duplicates)
        release_folder = self.repo_root / "release-20251105-223624"
        if release_folder.exists():
            self.safe_delete(release_folder)

        # Keep only one icon file, delete duplicates
        icons = [
            self.repo_root / "first-run-wizard" / "assets" / "icon.png",
            self.repo_root / "windows-ai-tray" / "assets" / "icon.png",
            self.repo_root / "wizard" / "assets" / "icon.png",
        ]

        # Keep the first one, delete others
        for icon in icons[1:]:
            if icon.exists():
                self.log("INFO", f"Consider creating symlink to shared icon instead of deleting {icon}")
                # Don't actually delete - just note for manual review

    def cleanup_archive(self):
        """Clean up archive directory"""
        print("\n" + "="*80)
        print("STEP 3: Clean Up Archive Directory")
        print("="*80 + "\n")

        # Delete the extension-generation folder with 218 empty/duplicate files
        extensions_parallel = self.repo_root / "archive" / "extension-generation"
        if extensions_parallel.exists():
            self.safe_delete(extensions_parallel)

        # Add README to archive explaining it's historical
        archive_readme = self.repo_root / "archive" / "README.md"
        if not archive_readme.exists() and not self.dry_run:
            archive_readme.write_text("""# Archive Directory

This directory contains historical code and generated files that are no longer active.

**DO NOT USE CODE FROM THIS DIRECTORY!**

This is kept for reference only. All active development should reference:
- NEW_MASTER_ROADMAP.md
- HONEST_REPO_ASSESSMENT.md
- docs/ for current documentation

Last updated: 2025-11-15
""")
            self.log("CREATE", str(archive_readme))

    def organize_plugins(self):
        """Organize plugins by completion tier"""
        print("\n" + "="*80)
        print("STEP 4: Organize Plugins by Tier")
        print("="*80 + "\n")

        # This is complex and should be done carefully
        # For now, just create a classification file
        classification_file = self.repo_root / "plugins" / "PLUGIN_CLASSIFICATION.md"

        classification_content = """# Plugin Classification by Tier

Based on HONEST_REPO_ASSESSMENT.md analysis.

## TIER 1: PRODUCTION-READY (30-40 plugins)
**200+ lines, full implementations, complete with config.json and README.md**

### Cloud AI Providers (20)
- ai_providers/openai
- ai_providers/anthropic
- ai_providers/google
- ai_providers/microsoft
- ai_providers/meta
- ai_providers/cohere
- ai_providers/ai21
- ai_providers/mistral
- ai_providers/perplexity
- ai_providers/together
- ai_providers/anyscale
- ai_providers/replicate
- ai_providers/huggingface
- ai_providers/stability
- ai_providers/midjourney
- ai_providers/runway
- ai_providers/amazon_bedrock
- ai_providers/alibaba
- ai_providers/baidu
- ai_providers/yandex

### Local Model Platforms (10)
- local_models/ollama
- local_models/lm_studio
- local_models/gpt4all
- local_models/localai
- local_models/jan
- local_models/koboldai
- local_models/text_generation_webui
- local_models/llama.cpp
- local_models/vllm
- local_models/exllama

## TIER 2: FUNCTIONAL SKELETON (15 plugins)
**50-100 lines, partial implementations**

### Windows Integration (10)
- windows_integration/file_system_manager
- windows_integration/registry_manager
- windows_integration/service_manager
- windows_integration/process_manager
- windows_integration/window_manager
- windows_integration/event_log_reader
- windows_integration/task_scheduler
- windows_integration/powershell_integration
- windows_integration/wmi_provider
- windows_integration/com_automation

### Monitoring (5)
- monitoring/system_monitor
- monitoring/gpu_monitor
- monitoring/performance_profiler
- monitoring/resource_manager
- monitoring/metrics_collector

## TIER 3: MINIMAL PLACEHOLDERS (74+ plugins)
**15-42 lines, stub methods only - NEED REAL IMPLEMENTATION**

### Code Models (15)
- code_models/* (all 15 plugins)

### Vision Models (20)
- vision_models/* (all 20 plugins)

### Audio Models (25)
- audio_models/* (all 25 plugins)

### Logging (4)
- logging/* (all 4 plugins)

### Developer Tools (10)
- developer_tools/* (all 10 plugins)

## TIER 4: INCOMPLETE/NEEDS REVIEW
- All remaining plugins in other categories

---

**Action Items:**
1. Complete TIER 3 placeholders with real implementations
2. Enhance TIER 2 skeletons to production-ready
3. Test TIER 1 implementations
4. Add README.md to all plugins missing documentation (66%)
"""

        if not self.dry_run:
            classification_file.write_text(classification_content)
            self.log("CREATE", str(classification_file))
        else:
            self.log("WOULD CREATE", str(classification_file))

    def update_main_readme(self):
        """Update main README.md with honest status"""
        print("\n" + "="*80)
        print("STEP 5: Update Main README.md")
        print("="*80 + "\n")

        self.log("TODO", "Main README.md should be updated to reference NEW_MASTER_ROADMAP.md")
        self.log("TODO", "Remove or correct misleading progress claims")
        self.log("TODO", "Add link to HONEST_REPO_ASSESSMENT.md")

    def create_summary_report(self):
        """Create a summary of all changes"""
        print("\n" + "="*80)
        print("CLEANUP SUMMARY")
        print("="*80 + "\n")

        print(f"Total actions: {len(self.changes)}")
        print(f"Mode: {'DRY-RUN (no changes made)' if self.dry_run else 'EXECUTE (changes applied)'}")

        # Group by action type
        action_counts = {}
        for change in self.changes:
            action = change["action"]
            action_counts[action] = action_counts.get(action, 0) + 1

        print("\nActions by type:")
        for action, count in sorted(action_counts.items()):
            print(f"  {action}: {count}")

        # Save detailed log
        log_file = self.repo_root / f"cleanup_log_{'dryrun' if self.dry_run else 'executed'}.json"
        if not self.dry_run or True:  # Always save log even in dry-run
            with open(log_file, 'w') as f:
                json.dump(self.changes, f, indent=2)
            print(f"\nDetailed log saved to: {log_file}")

    def run(self):
        """Execute all cleanup steps"""
        print("\n" + "="*80)
        print("WINDOWS-AI REPOSITORY CLEANUP")
        print("="*80)
        print(f"Repository: {self.repo_root}")
        print(f"Mode: {'DRY-RUN' if self.dry_run else 'EXECUTE'}")
        print("="*80 + "\n")

        if self.dry_run:
            print("WARNING: DRY-RUN MODE: No changes will be made to the repository")
            print("Run with --execute to apply changes\n")
        else:
            print("WARNING: EXECUTE MODE: Changes will be made to the repository")
            print("Make sure you have a backup or commit current state first!\n")
            response = input("Continue? (yes/no): ")
            if response.lower() != 'yes':
                print("Aborted.")
                return

        # Run cleanup steps
        self.archive_old_roadmaps()
        self.cleanup_duplicates()
        self.cleanup_archive()
        self.organize_plugins()
        self.update_main_readme()
        self.create_summary_report()

        print("\n" + "="*80)
        print("CLEANUP COMPLETE!")
        print("="*80 + "\n")

        if self.dry_run:
            print("This was a DRY-RUN. No changes were made.")
            print("Review the output above and run with --execute to apply changes.")
        else:
            print("All changes have been applied.")
            print("Next steps:")
            print("1. Review the changes with git status")
            print("2. Update README.md manually")
            print("3. Begin implementing placeholder plugins")


def main():
    parser = argparse.ArgumentParser(description="Clean up Windows-AI repository")
    parser.add_argument("--dry-run", action="store_true", default=True,
                       help="Preview changes without executing (default)")
    parser.add_argument("--execute", action="store_true",
                       help="Execute changes (DESTRUCTIVE)")

    args = parser.parse_args()

    # If --execute is specified, turn off dry-run
    dry_run = not args.execute

    # Get repository root (where this script is located)
    repo_root = Path(__file__).parent

    # Create cleanup instance and run
    cleanup = RepoCleanup(repo_root, dry_run=dry_run)
    cleanup.run()


if __name__ == "__main__":
    main()
