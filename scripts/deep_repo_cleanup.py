#!/usr/bin/env python3
"""
Deep Repository Cleanup and Organization Script
Analyzes, organizes, and cleans up the Windows-AI repository
"""

import os
import shutil
from pathlib import Path
from collections import defaultdict
import json
from datetime import datetime

class RepoAnalyzer:
    def __init__(self, repo_root: Path):
        self.repo_root = repo_root
        self.analysis = {
            'timestamp': datetime.now().isoformat(),
            'total_files': 0,
            'total_dirs': 0,
            'duplicates': [],
            'empty_dirs': [],
            'temp_files': [],
            'generated_files': [],
            'file_types': defaultdict(int),
            'large_files': [],
            'roadmap_files': [],
            'plugin_files': [],
            'test_files': [],
            'docs_files': []
        }
    
    def scan_repository(self):
        """Comprehensive repository scan"""
        print("🔍 Scanning repository...")
        
        for root, dirs, files in os.walk(self.repo_root):
            root_path = Path(root)
            
            # Skip common ignore directories
            dirs[:] = [d for d in dirs if d not in {
                '.git', '__pycache__', 'node_modules', '.venv', 'venv',
                'dist', 'build', '.pytest_cache', '.mypy_cache'
            }]
            
            self.analysis['total_dirs'] += len(dirs)
            
            # Check for empty directories
            if not files and not dirs:
                self.analysis['empty_dirs'].append(str(root_path.relative_to(self.repo_root)))
            
            for file in files:
                self.analysis['total_files'] += 1
                file_path = root_path / file
                relative_path = file_path.relative_to(self.repo_root)
                
                # Track file type
                ext = file_path.suffix.lower()
                self.analysis['file_types'][ext if ext else 'no_extension'] += 1
                
                # Identify roadmap files
                if 'roadmap' in file.lower():
                    self.analysis['roadmap_files'].append(str(relative_path))
                
                # Identify plugin files
                if 'plugin' in str(relative_path).lower():
                    self.analysis['plugin_files'].append(str(relative_path))
                
                # Identify test files
                if 'test' in file.lower() or 'spec' in file.lower():
                    self.analysis['test_files'].append(str(relative_path))
                
                # Identify docs
                if str(relative_path).startswith('docs'):
                    self.analysis['docs_files'].append(str(relative_path))
                
                # Check for temporary/generated files
                if file.endswith(('.tmp', '.log', '.cache', '.pyc', '.pyo')):
                    self.analysis['temp_files'].append(str(relative_path))
                
                # Track large files (> 1MB)
                try:
                    size = file_path.stat().st_size
                    if size > 1_000_000:
                        self.analysis['large_files'].append({
                            'path': str(relative_path),
                            'size_mb': round(size / 1_000_000, 2)
                        })
                except:
                    pass
        
        print(f"✅ Scan complete: {self.analysis['total_files']} files, {self.analysis['total_dirs']} directories")
    
    def find_duplicates(self):
        """Find duplicate files by content"""
        print("\n🔍 Finding duplicate files...")
        import hashlib
        
        file_hashes = defaultdict(list)
        
        for root, dirs, files in os.walk(self.repo_root):
            dirs[:] = [d for d in dirs if d not in {
                '.git', '__pycache__', 'node_modules', '.venv'
            }]
            
            for file in files:
                file_path = Path(root) / file
                try:
                    # Skip large files for performance
                    if file_path.stat().st_size > 10_000_000:
                        continue
                    
                    with open(file_path, 'rb') as f:
                        file_hash = hashlib.md5(f.read()).hexdigest()
                    
                    file_hashes[file_hash].append(str(file_path.relative_to(self.repo_root)))
                except:
                    pass
        
        # Find duplicates
        for file_hash, paths in file_hashes.items():
            if len(paths) > 1:
                self.analysis['duplicates'].append({
                    'count': len(paths),
                    'files': paths
                })
        
        print(f"✅ Found {len(self.analysis['duplicates'])} sets of duplicate files")
    
    def generate_report(self):
        """Generate comprehensive analysis report"""
        report = []
        report.append("=" * 80)
        report.append("WINDOWS-AI REPOSITORY DEEP ANALYSIS")
        report.append("=" * 80)
        report.append(f"Generated: {self.analysis['timestamp']}")
        report.append("")
        
        # Overview
        report.append("## OVERVIEW")
        report.append(f"Total Files: {self.analysis['total_files']:,}")
        report.append(f"Total Directories: {self.analysis['total_dirs']:,}")
        report.append(f"Empty Directories: {len(self.analysis['empty_dirs'])}")
        report.append(f"Temporary Files: {len(self.analysis['temp_files'])}")
        report.append(f"Duplicate File Sets: {len(self.analysis['duplicates'])}")
        report.append("")
        
        # File types
        report.append("## FILE TYPE DISTRIBUTION")
        for ext, count in sorted(self.analysis['file_types'].items(), 
                                 key=lambda x: x[1], reverse=True)[:20]:
            report.append(f"  {ext}: {count:,}")
        report.append("")
        
        # Roadmap files
        report.append(f"## ROADMAP FILES ({len(self.analysis['roadmap_files'])})")
        for path in sorted(self.analysis['roadmap_files']):
            report.append(f"  - {path}")
        report.append("")
        
        # Large files
        report.append(f"## LARGE FILES (>1MB) - {len(self.analysis['large_files'])}")
        for file_info in sorted(self.analysis['large_files'], 
                               key=lambda x: x['size_mb'], reverse=True)[:20]:
            report.append(f"  - {file_info['path']} ({file_info['size_mb']} MB)")
        report.append("")
        
        # Duplicates
        if self.analysis['duplicates']:
            report.append(f"## DUPLICATE FILES ({len(self.analysis['duplicates'])} sets)")
            for i, dup in enumerate(self.analysis['duplicates'][:10], 1):
                report.append(f"\nSet {i} ({dup['count']} copies):")
                for path in dup['files']:
                    report.append(f"  - {path}")
        
        # Empty directories
        if self.analysis['empty_dirs']:
            report.append(f"\n## EMPTY DIRECTORIES ({len(self.analysis['empty_dirs'])})")
            for path in sorted(self.analysis['empty_dirs'])[:20]:
                report.append(f"  - {path}")
        
        return "\n".join(report)
    
    def save_analysis(self, output_file: Path):
        """Save analysis to JSON"""
        with open(output_file, 'w') as f:
            json.dump(self.analysis, f, indent=2)
        print(f"✅ Analysis saved to: {output_file}")

def main():
    repo_root = Path(__file__).parent.parent
    
    print("=" * 80)
    print("WINDOWS-AI DEEP REPOSITORY CLEANUP")
    print("=" * 80)
    print()
    
    # Run analysis
    analyzer = RepoAnalyzer(repo_root)
    analyzer.scan_repository()
    analyzer.find_duplicates()
    
    # Generate and display report
    report = analyzer.generate_report()
    print("\n" + report)
    
    # Save analysis
    analysis_file = repo_root / "REPO_ANALYSIS_DETAILED.json"
    analyzer.save_analysis(analysis_file)
    
    # Save report
    report_file = repo_root / "REPO_ANALYSIS_REPORT.md"
    report_file.write_text(report, encoding='utf-8')
    print(f"✅ Report saved to: {report_file}")
    
    print("\n" + "=" * 80)
    print("NEXT STEPS:")
    print("=" * 80)
    print("1. Review REPO_ANALYSIS_REPORT.md")
    print("2. Review duplicate files and decide which to keep")
    print("3. Remove empty directories")
    print("4. Clean up temporary files")
    print("5. Consolidate roadmap files")
    print("6. Organize plugin files by category")
    print("7. Begin systematic implementation of COMPLETE_ROADMAP_TO_100.md")

if __name__ == "__main__":
    main()
