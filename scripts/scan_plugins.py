"""
Plugin Scanner - Audit all plugins in Windows-AI

This script scans and analyzes all plugin files to create a comprehensive audit.
"""

import os
import json
import ast
from pathlib import Path
from typing import Dict, List, Any
import re

def analyze_plugin_file(file_path: Path) -> Dict[str, Any]:
    """Analyze a single plugin file"""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()

        # Basic metrics
        lines = content.split('\n')
        code_lines = [l for l in lines if l.strip() and not l.strip().startswith('#')]

        # Check for class definition
        has_plugin_class = 'class Plugin' in content
        has_metadata = 'get_metadata' in content or 'PluginMetadata' in content
        has_execute = 'async def execute' in content or 'def execute' in content
        has_init = '__init__' in content

        # Check for API key handling
        has_api_key = bool(re.search(r'(api_key|API_KEY|apikey|token|TOKEN)', content, re.I))
        has_env_vars = bool(re.search(r'(os\.getenv|os\.environ)', content))

        # Check for error handling
        has_try_except = 'try:' in content and 'except' in content
        has_logging = 'logging' in content or 'logger' in content

        # Check for docstrings
        has_docstring = '"""' in content or "'''" in content

        # Determine if stub/template
        is_stub = any([
            '{{' in content and '}}' in content,  # Template markers
            'pass  # TODO' in content,
            'NotImplementedError' in content,
            len(code_lines) < 30 and not has_execute
        ])

        # Determine completeness
        completeness = 'complete' if (has_plugin_class and has_execute and has_metadata and len(code_lines) > 50) else 'partial' if has_plugin_class else 'stub'

        return {
            'path': str(file_path),
            'name': file_path.stem,
            'size': len(content),
            'total_lines': len(lines),
            'code_lines': len(code_lines),
            'has_plugin_class': has_plugin_class,
            'has_metadata': has_metadata,
            'has_execute': has_execute,
            'has_init': has_init,
            'has_api_key_handling': has_api_key,
            'has_env_vars': has_env_vars,
            'has_error_handling': has_try_except,
            'has_logging': has_logging,
            'has_docstring': has_docstring,
            'is_stub': is_stub,
            'completeness': completeness
        }
    except Exception as e:
        return {
            'path': str(file_path),
            'name': file_path.stem,
            'error': str(e),
            'completeness': 'error'
        }

def scan_plugins_directory(base_dir: Path) -> Dict[str, Any]:
    """Scan all plugins in the directory"""
    results = {
        'total_files': 0,
        'by_category': {},
        'by_completeness': {'complete': [], 'partial': [], 'stub': [], 'error': []},
        'files': []
    }

    # Scan all Python files
    for py_file in base_dir.rglob('*.py'):
        # Skip __init__ and __pycache__
        if py_file.name.startswith('__') or '__pycache__' in str(py_file):
            continue

        results['total_files'] += 1

        # Analyze the file
        analysis = analyze_plugin_file(py_file)
        results['files'].append(analysis)

        # Categorize
        category = py_file.parent.name
        if category not in results['by_category']:
            results['by_category'][category] = []
        results['by_category'][category].append(analysis['name'])

        # Group by completeness
        completeness = analysis.get('completeness', 'error')
        results['by_completeness'][completeness].append(analysis['name'])

    return results

def main():
    """Main scanning function"""
    base_dir = Path(r'C:\Users\antho\Windows-AI\windows_ai\plugins\builtin')

    print("Scanning plugins directory...")
    print(f"Base directory: {base_dir}")
    print()

    if not base_dir.exists():
        print(f"ERROR: Directory does not exist: {base_dir}")
        return

    results = scan_plugins_directory(base_dir)

    # Save results
    output_file = Path(r'C:\Users\antho\Windows-AI\plugin_audit.json')
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(results, f, indent=2)

    print(f"✓ Scanned {results['total_files']} plugin files")
    print()

    print("By Category:")
    for category, files in sorted(results['by_category'].items()):
        print(f"  {category}: {len(files)} files")
    print()

    print("By Completeness:")
    for status, files in results['by_completeness'].items():
        print(f"  {status}: {len(files)} files")
    print()

    print(f"✓ Results saved to: {output_file}")

    # Generate summary report
    summary_file = Path(r'C:\Users\antho\Windows-AI\plugin_audit_summary.txt')
    with open(summary_file, 'w', encoding='utf-8') as f:
        f.write("WINDOWS-AI PLUGIN AUDIT SUMMARY\n")
        f.write("=" * 80 + "\n\n")

        f.write(f"Total Plugin Files: {results['total_files']}\n\n")

        f.write("COMPLETENESS BREAKDOWN:\n")
        f.write("-" * 80 + "\n")
        for status, files in results['by_completeness'].items():
            f.write(f"{status.upper()}: {len(files)} plugins\n")
        f.write("\n")

        f.write("CATEGORY BREAKDOWN:\n")
        f.write("-" * 80 + "\n")
        for category, files in sorted(results['by_category'].items()):
            f.write(f"{category}: {len(files)} plugins\n")
        f.write("\n")

        f.write("STUB PLUGINS (Need Implementation):\n")
        f.write("-" * 80 + "\n")
        for file in sorted(results['by_completeness']['stub']):
            f.write(f"  - {file}\n")
        f.write("\n")

        f.write("PARTIAL PLUGINS (Need Completion):\n")
        f.write("-" * 80 + "\n")
        for file in sorted(results['by_completeness']['partial']):
            f.write(f"  - {file}\n")
        f.write("\n")

        f.write("COMPLETE PLUGINS (Production Ready):\n")
        f.write("-" * 80 + "\n")
        for file in sorted(results['by_completeness']['complete']):
            f.write(f"  - {file}\n")

    print(f"✓ Summary saved to: {summary_file}")

if __name__ == '__main__':
    main()
