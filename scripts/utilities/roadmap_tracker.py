#!/usr/bin/env python3
"""
Roadmap Completion Tracker
Tracks progress across all 1000 roadmap upgrades and generates completion reports
"""

import os
import re
from pathlib import Path
from typing import Dict, List, Set, Tuple
from collections import defaultdict

class RoadmapTracker:
    def __init__(self, repo_root: Path):
        self.repo_root = repo_root
        self.roadmap_file = repo_root / "docs" / "ROADMAP.md"
        self.phases = {
            1: {"range": [(1, 100), (501, 600)], "name": "Foundation"},
            2: {"range": [(101, 200), (601, 700)], "name": "Core Intelligence"},
            3: {"range": [(201, 300)], "name": "Advanced Intelligence"},
            4: {"range": [(301, 400)], "name": "Robustness & Security"},
            5: {"range": [(401, 500)], "name": "Ecosystem & Expansion"}
        }
        
    def parse_roadmap_upgrades(self) -> Dict[int, str]:
        """Extract all upgrade descriptions from roadmap"""
        upgrades = {}
        content = self.roadmap_file.read_text(encoding='utf-8')
        
        # Match: **Upgrade XXX:** Description
        pattern = r'\*\*Upgrade (\d+):\*\*\s+(.+?)(?=\n\*\*Upgrade|\n##|\Z)'
        matches = re.findall(pattern, content, re.DOTALL)
        
        for num, desc in matches:
            upgrades[int(num)] = desc.strip()
        
        return upgrades
    
    def scan_implementation_status(self) -> Dict[int, bool]:
        """Scan repository to determine which upgrades are implemented"""
        status = {}
        upgrades = self.parse_roadmap_upgrades()
        
        for upgrade_num, description in upgrades.items():
            status[upgrade_num] = self.is_upgrade_implemented(upgrade_num, description)
        
        return status
    
    def is_upgrade_implemented(self, num: int, description: str) -> bool:
        """Check if a specific upgrade is implemented"""
        
        # Extract file paths from description
        # Pattern: scripts/path/file.py, docs/path/file.md, etc.
        path_pattern = r'`([a-zA-Z0-9_/.-]+\.[a-z]+)`'
        paths = re.findall(path_pattern, description)
        
        if not paths:
            return False
        
        # Check if at least one file exists
        for path_str in paths:
            file_path = self.repo_root / path_str
            if file_path.exists():
                return True
        
        return False
    
    def generate_report(self) -> str:
        """Generate comprehensive roadmap completion report"""
        upgrades = self.parse_roadmap_upgrades()
        status = self.scan_implementation_status()
        
        report = []
        report.append("=" * 80)
        report.append("WINDOWS-AI ROADMAP COMPLETION REPORT")
        report.append("=" * 80)
        report.append("")
        
        # Overall statistics
        total = len(upgrades)
        completed = sum(1 for s in status.values() if s)
        percentage = (completed / total * 100) if total > 0 else 0
        
        report.append(f"Overall Progress: {completed}/{total} ({percentage:.1f}%)")
        report.append("")
        
        # Progress bar
        bar_length = 50
        filled = int(bar_length * completed / total)
        bar = "█" * filled + "░" * (bar_length - filled)
        report.append(f"[{bar}] {percentage:.1f}%")
        report.append("")
        report.append("=" * 80)
        
        # Per-phase breakdown
        for phase_num, phase_info in sorted(self.phases.items()):
            report.append("")
            report.append(f"Phase {phase_num}: {phase_info['name']}")
            report.append("-" * 80)
            
            phase_upgrades = []
            for start, end in phase_info['range']:
                phase_upgrades.extend(range(start, end + 1))
            
            phase_total = len([u for u in phase_upgrades if u in upgrades])
            phase_completed = sum(1 for u in phase_upgrades if status.get(u, False))
            phase_pct = (phase_completed / phase_total * 100) if phase_total > 0 else 0
            
            report.append(f"  Progress: {phase_completed}/{phase_total} ({phase_pct:.1f}%)")
            
            # Mini progress bar
            mini_bar_length = 40
            mini_filled = int(mini_bar_length * phase_completed / phase_total) if phase_total > 0 else 0
            mini_bar = "█" * mini_filled + "░" * (mini_bar_length - mini_filled)
            report.append(f"  [{mini_bar}]")
            
            # List incomplete upgrades (first 5)
            incomplete = [u for u in phase_upgrades if u in upgrades and not status.get(u, False)]
            if incomplete:
                report.append(f"  Pending: {incomplete[:5]}" + 
                            (f" ... ({len(incomplete)} total)" if len(incomplete) > 5 else ""))
        
        report.append("")
        report.append("=" * 80)
        
        return "\n".join(report)
    
    def get_next_upgrades(self, count: int = 10) -> List[Tuple[int, str]]:
        """Get next N upgrades to implement"""
        upgrades = self.parse_roadmap_upgrades()
        status = self.scan_implementation_status()
        
        pending = [(num, desc) for num, desc in sorted(upgrades.items()) 
                   if not status.get(num, False)]
        
        return pending[:count]
    
    def export_todo_list(self, output_file: Path):
        """Export pending upgrades as TODO list"""
        pending = self.get_next_upgrades(count=1000)
        
        lines = []
        lines.append("# Windows-AI Roadmap TODO List")
        lines.append(f"\nTotal pending: {len(pending)} upgrades\n")
        
        current_phase = None
        for num, desc in pending:
            # Determine phase
            phase = None
            for p_num, p_info in self.phases.items():
                for start, end in p_info['range']:
                    if start <= num <= end:
                        phase = (p_num, p_info['name'])
                        break
            
            if phase and phase != current_phase:
                current_phase = phase
                lines.append(f"\n## Phase {phase[0]}: {phase[1]}\n")
            
            # Extract file path from description
            path_match = re.search(r'`([a-zA-Z0-9_/.-]+\.[a-z]+)`', desc)
            path_str = path_match.group(1) if path_match else "unknown"
            
            lines.append(f"- [ ] **Upgrade {num:03d}**: {path_str}")
            lines.append(f"  {desc[:100]}...")
        
        output_file.write_text("\n".join(lines), encoding='utf-8')
        print(f"Exported TODO list to: {output_file}")

def main():
    repo_root = Path(__file__).parent.parent
    tracker = RoadmapTracker(repo_root)
    
    # Generate and display report
    report = tracker.generate_report()
    print(report)
    
    # Export TODO list
    todo_file = repo_root / "docs" / "ROADMAP_TODO.md"
    tracker.export_todo_list(todo_file)
    
    # Show next 10 items
    print("\n" + "=" * 80)
    print("NEXT 10 UPGRADES TO IMPLEMENT")
    print("=" * 80)
    next_items = tracker.get_next_upgrades(10)
    for num, desc in next_items:
        path_match = re.search(r'`([a-zA-Z0-9_/.-]+\.[a-z]+)`', desc)
        path_str = path_match.group(1) if path_match else "unknown"
        print(f"\n{num:03d}. {path_str}")
        print(f"     {desc[:150]}...")

if __name__ == "__main__":
    main()
