"""
Master Plan Execution Script 1: Complete Repository Scanner
Scans 100% of files and directories with category classification

Repository Statistics Discovered:
- Total relevant files: 9,196
- Total directories: 449
- Python files: 8,219
- Test files: 108
- Documentation files: 1,025
"""

import os
import json
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Set, Optional
from dataclasses import dataclass, asdict
import hashlib

@dataclass
class FileInfo:
    path: str
    category: str
    role: str
    size_bytes: int
    extension: str
    has_tests: bool = False
    has_docs: bool = False
    completion_score: int = 0

@dataclass
class DirectoryInfo:
    path: str
    category: str
    role: str
    priority: str
    required_action: str
    file_count: int
    completion_score: int
    notes: str

class RepositoryScanner:
    """Complete repository scanner with 100% file coverage"""
    
    def __init__(self, repo_root: str):
        self.repo_root = Path(repo_root)
        self.files: List[FileInfo] = []
        self.directories: List[DirectoryInfo] = []
        self.stats = {
            "scan_date": datetime.now().isoformat(),
            "total_files": 0,
            "total_directories": 0,
            "total_size_bytes": 0,
            "files_by_extension": {},
            "files_by_category": {},
            "completion_scores": {},
        }
        
        # Category patterns for classification
        self.category_patterns = {
            "core_backend": [
                "windows_ai/core/",
                "windows_ai/frameworks/",
                "windows_ai/orchestrator",
                "src/windows_ai/core/"
            ],
            "plugins": [
                "windows_ai/plugins/",
                "src/plugins/",
                "windows_ai/builtin_plugins/"
            ],
            "agents": [
                "windows_ai/agents/",
                "agenthub/",
                "agents/",
                "windows-ai-agent/"
            ],
            "api": [
                "windows_ai/api/",
                "src/api/",
                "backends/api/"
            ],
            "gui": [
                "windows_ai/gui/",
                "apps/gui/",
                "gui/",
                "ui/",
                "control_center/"
            ],
            "cli": [
                "windows_ai/cli/",
                "apps/cli/",
                "terminal/"
            ],
            "tests": [
                "tests/",
                "test_",
                "_test.py",
                "pytest"
            ],
            "docs": [
                "docs/",
                "README",
                ".md",
                "ARCHITECTURE",
                "ROADMAP"
            ],
            "scripts": [
                "scripts/",
                "tools/",
                "automation/"
            ],
            "config": [
                "config/",
                ".env",
                ".json",
                ".yaml",
                ".toml",
                ".ini"
            ],
            "integrations": [
                "windows_ai/integrations/",
                "cloud_sync/",
                "iot/",
                "mobile/"
            ],
            "installer": [
                "install/",
                "installer/",
                "setup.py",
                "build.py",
                "nssm-"
            ],
            "archive": [
                ".archive/",
                "archive/",
                "roadmap-archive/"
            ],
            "templates": [
                "templates/",
                "specs/",
                "wizard/"
            ],
            "build": [
                "build/",
                "dist/",
                ".egg-info/"
            ],
            "cache": [
                "__pycache__/",
                ".pytest_cache/",
                ".mypy_cache/",
                "node_modules/"
            ]
        }
        
        self.skip_dirs = {
            ".git", "__pycache__", ".pytest_cache", ".mypy_cache",
            "node_modules", ".venv", "venv", "env", ".env",
            "dist", "build", ".egg-info"
        }
        
    def scan(self) -> Dict:
        """Execute full repository scan"""
        print("="*80)
        print("🔍 WINDOWS-AI REPOSITORY SCANNER")
        print("="*80)
        print(f"Repository Root: {self.repo_root}")
        print(f"Started: {self.stats['scan_date']}")
        print("="*80 + "\n")
        
        # Scan all files and directories
        for root, dirs, files in os.walk(self.repo_root):
            # Filter directories
            dirs[:] = [d for d in dirs if d not in self.skip_dirs]
            
            rel_root = Path(root).relative_to(self.repo_root)
            
            # Process directory
            self._process_directory(rel_root, len(files))
            
            # Process files
            for filename in files:
                file_path = Path(root) / filename
                self._process_file(file_path, rel_root)
        
        # Calculate completion scores
        self._calculate_completion_scores()
        
        # Generate statistics
        self._generate_statistics()
        
        print("\n" + "="*80)
        print("✅ SCAN COMPLETE")
        print("="*80)
        
        return self.stats
    
    def _process_directory(self, rel_path: Path, file_count: int):
        """Process a directory and classify it"""
        if rel_path == Path("."):
            return
            
        self.stats["total_directories"] += 1
        
        category = self._categorize_path(str(rel_path))
        role = self._determine_role(str(rel_path), category)
        priority = self._determine_priority(category, role)
        action = self._determine_action(category, role)
        
        dir_info = DirectoryInfo(
            path=str(rel_path),
            category=category,
            role=role,
            priority=priority,
            required_action=action,
            file_count=file_count,
            completion_score=0,  # Calculated later
            notes=f"{file_count} files"
        )
        
        self.directories.append(dir_info)
    
    def _process_file(self, file_path: Path, rel_root: Path):
        """Process a single file"""
        try:
            stat = file_path.stat()
            ext = file_path.suffix.lower() or "no_extension"
            rel_path = file_path.relative_to(self.repo_root)
            
            self.stats["total_files"] += 1
            self.stats["total_size_bytes"] += stat.st_size
            
            # Track by extension
            self.stats["files_by_extension"][ext] = \
                self.stats["files_by_extension"].get(ext, 0) + 1
            
            # Categorize
            category = self._categorize_path(str(rel_path))
            role = self._determine_role(str(rel_path), category)
            
            self.stats["files_by_category"][category] = \
                self.stats["files_by_category"].get(category, 0) + 1
            
            # Create file info
            file_info = FileInfo(
                path=str(rel_path),
                category=category,
                role=role,
                size_bytes=stat.st_size,
                extension=ext
            )
            
            self.files.append(file_info)
            
        except Exception as e:
            print(f"⚠️  Error processing {file_path}: {e}")
    
    def _categorize_path(self, path_str: str) -> str:
        """Categorize a path based on patterns"""
        path_lower = path_str.lower()
        
        for category, patterns in self.category_patterns.items():
            for pattern in patterns:
                if pattern.lower() in path_lower:
                    return category
        
        return "other"
    
    def _determine_role(self, path_str: str, category: str) -> str:
        """Determine role of a file/directory"""
        path_lower = path_str.lower()
        
        if category == "archive":
            return "archive"
        elif category == "cache" or category == "build":
            return "generated"
        elif category == "templates":
            return "template"
        elif "example" in path_lower or "sample" in path_lower:
            return "example"
        elif "test" in path_lower:
            return "test"
        elif "stub" in path_lower or "placeholder" in path_lower:
            return "stub"
        else:
            return "production"
    
    def _determine_priority(self, category: str, role: str) -> str:
        """Determine priority level"""
        if role in ["archive", "generated", "cache"]:
            return "LOW"
        elif category in ["core_backend", "plugins", "agents", "api"]:
            return "HIGH"
        elif category in ["gui", "tests", "docs"]:
            return "MEDIUM"
        else:
            return "LOW"
    
    def _determine_action(self, category: str, role: str) -> str:
        """Determine required action"""
        if role == "generated":
            return "ignore"
        elif role == "archive":
            return "keep"
        elif category == "docs" and role == "production":
            return "consolidate"
        elif category == "gui":
            return "refactor"
        elif category == "config":
            return "unify"
        else:
            return "keep"
    
    def _calculate_completion_scores(self):
        """Calculate completion scores for major directories"""
        major_paths = {
            "windows_ai/core": "core_backend",
            "windows_ai/plugins": "plugins",
            "windows_ai/agents": "agents",
            "windows_ai/api": "api",
            "windows_ai/gui": "gui",
            "tests": "tests",
            "docs": "docs",
            "install": "installer"
        }
        
        for path_str, expected_category in major_paths.items():
            full_path = self.repo_root / path_str
            if full_path.exists():
                score = self._calculate_dir_score(full_path)
                self.stats["completion_scores"][path_str] = {
                    "category": expected_category,
                    "score": score,
                    "status": self._get_score_label(score)
                }
    
    def _calculate_dir_score(self, dir_path: Path) -> int:
        """Calculate completion score (0-100) for a directory"""
        if not dir_path.exists():
            return 0
        
        py_files = list(dir_path.rglob("*.py"))
        if not py_files:
            return 10  # Directory exists but empty
        
        score = 50  # Base score for having code
        
        # Check for proper package structure
        if (dir_path / "__init__.py").exists():
            score += 10
        
        # Check for tests
        parent_name = dir_path.name
        test_patterns = [
            self.repo_root / "tests" / f"test_{parent_name}.py",
            self.repo_root / "tests" / parent_name,
            dir_path / "tests"
        ]
        
        has_tests = any(p.exists() for p in test_patterns)
        if has_tests:
            score += 15
        
        # Check for documentation
        doc_files = list(dir_path.rglob("*.md"))
        if doc_files:
            score += 10
        
        # Penalize for TODOs and stubs
        stub_count = 0
        sample_size = min(20, len(py_files))
        
        for py_file in py_files[:sample_size]:
            try:
                content = py_file.read_text(encoding='utf-8', errors='ignore')
                if any(marker in content for marker in ["TODO", "FIXME", "XXX", "pass  # stub"]):
                    stub_count += 1
            except:
                pass
        
        if sample_size > 0:
            stub_ratio = stub_count / sample_size
            if stub_ratio > 0.5:
                score -= 20
            elif stub_ratio > 0.3:
                score -= 10
        
        return max(0, min(100, score))
    
    def _get_score_label(self, score: int) -> str:
        """Get label for completion score"""
        if score >= 80:
            return "✅ Production Ready"
        elif score >= 60:
            return "🟡 Mostly Complete"
        elif score >= 40:
            return "🟠 Partial"
        elif score >= 20:
            return "🔴 Stub/Skeleton"
        else:
            return "❌ Empty/Missing"
    
    def _generate_statistics(self):
        """Generate summary statistics"""
        self.stats["summary"] = {
            "total_python_files": self.stats["files_by_extension"].get(".py", 0),
            "total_test_files": sum(1 for f in self.files if "test" in f.path.lower()),
            "total_doc_files": self.stats["files_by_extension"].get(".md", 0),
            "total_config_files": self.stats["files_by_category"].get("config", 0),
            "total_size_mb": round(self.stats["total_size_bytes"] / (1024 * 1024), 2),
            "production_ready_dirs": sum(
                1 for score_info in self.stats["completion_scores"].values()
                if score_info["score"] >= 80
            ),
            "needs_work_dirs": sum(
                1 for score_info in self.stats["completion_scores"].values()
                if score_info["score"] < 60
            )
        }
    
    def export_results(self, output_dir: str):
        """Export scan results to JSON and Markdown"""
        output_path = Path(output_dir)
        output_path.mkdir(parents=True, exist_ok=True)
        
        # Export JSON
        json_file = output_path / "repository_scan_results.json"
        with open(json_file, 'w', encoding='utf-8') as f:
            json.dump(self.stats, f, indent=2)
        
        # Export category mapping as markdown
        md_file = output_path / "CATEGORY_MAPPING.md"
        self._export_category_mapping_md(md_file)
        
        # Export completion scores as markdown
        scores_file = output_path / "COMPLETION_SCORES.md"
        self._export_completion_scores_md(scores_file)
        
        print(f"\n📄 Results exported to:")
        print(f"   - {json_file}")
        print(f"   - {md_file}")
        print(f"   - {scores_file}")
    
    def _export_category_mapping_md(self, output_file: Path):
        """Export category mapping table to Markdown"""
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write("# Windows-AI Directory Category Mapping\n\n")
            f.write(f"**Generated:** {datetime.now().isoformat()}\n")
            f.write(f"**Total Directories:** {len(self.directories)}\n\n")
            f.write("## Classification Table\n\n")
            f.write("| Path | Category | Role | Priority | Action | Files | Notes |\n")
            f.write("|------|----------|------|----------|--------|-------|-------|\n")
            
            # Sort by priority then path
            priority_order = {"HIGH": 0, "MEDIUM": 1, "LOW": 2}
            sorted_dirs = sorted(
                self.directories,
                key=lambda d: (priority_order.get(d.priority, 3), d.path)
            )
            
            for dir_info in sorted_dirs:
                f.write(
                    f"| `{dir_info.path}` | {dir_info.category} | {dir_info.role} | "
                    f"**{dir_info.priority}** | {dir_info.required_action} | "
                    f"{dir_info.file_count} | {dir_info.notes} |\n"
                )
    
    def _export_completion_scores_md(self, output_file: Path):
        """Export completion scores to Markdown"""
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write("# Windows-AI Folder Completion Scores\n\n")
            f.write(f"**Generated:** {datetime.now().isoformat()}\n\n")
            f.write("## Major Directories Assessment\n\n")
            f.write("| Directory | Category | Score | Status |\n")
            f.write("|-----------|----------|-------|--------|\n")
            
            for path, info in sorted(self.stats["completion_scores"].items()):
                f.write(
                    f"| `{path}` | {info['category']} | "
                    f"**{info['score']}%** | {info['status']} |\n"
                )
            
            f.write("\n## Score Legend\n\n")
            f.write("- **80-100%**: ✅ Production Ready - Full implementation with tests and docs\n")
            f.write("- **60-79%**: 🟡 Mostly Complete - Working code, may need tests/docs\n")
            f.write("- **40-59%**: 🟠 Partial - Some implementation, significant work needed\n")
            f.write("- **20-39%**: 🔴 Stub/Skeleton - Basic structure only\n")
            f.write("- **0-19%**: ❌ Empty/Missing - Not implemented\n")
    
    def print_summary(self):
        """Print scan summary to console"""
        print("\n" + "="*80)
        print("📊 SCAN SUMMARY")
        print("="*80)
        
        summary = self.stats["summary"]
        print(f"\n📁 Repository Overview:")
        print(f"   Total Files: {self.stats['total_files']:,}")
        print(f"   Total Directories: {self.stats['total_directories']:,}")
        print(f"   Total Size: {summary['total_size_mb']:,.2f} MB")
        
        print(f"\n🐍 Python Code:")
        print(f"   Python Files: {summary['total_python_files']:,}")
        print(f"   Test Files: {summary['total_test_files']:,}")
        print(f"   Test Coverage: {(summary['total_test_files'] / summary['total_python_files'] * 100):.1f}%")
        
        print(f"\n📚 Documentation:")
        print(f"   Markdown Files: {summary['total_doc_files']:,}")
        
        print(f"\n📊 Files by Category:")
        for category, count in sorted(
            self.stats['files_by_category'].items(),
            key=lambda x: x[1],
            reverse=True
        )[:10]:
            print(f"   {category}: {count:,}")
        
        print(f"\n📈 Completion Scores:")
        print(f"   Production Ready: {summary['production_ready_dirs']}")
        print(f"   Needs Work: {summary['needs_work_dirs']}")
        
        for path, info in sorted(self.stats["completion_scores"].items()):
            print(f"   {path}: {info['score']}% - {info['status']}")


def main():
    """Main execution function"""
    repo_root = r"c:\Users\antho\Windows-AI"
    output_dir = r"c:\Users\antho\Windows-AI\docs\master_plan"
    
    scanner = RepositoryScanner(repo_root)
    results = scanner.scan()
    scanner.print_summary()
    scanner.export_results(output_dir)
    
    print("\n" + "="*80)
    print("✅ REPOSITORY SCAN COMPLETE")
    print("="*80)


if __name__ == "__main__":
    main()
