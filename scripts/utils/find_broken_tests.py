#!/usr/bin/env python
"""Find test files with import errors"""
import os
import subprocess
import sys

def find_broken_tests(test_dir="tests"):
    """Find all test files with import errors"""
    broken_files = []
    
    for root, dirs, files in os.walk(test_dir):
        # Skip __pycache__ directories
        dirs[:] = [d for d in dirs if d != '__pycache__']
        
        for file in files:
            if file.startswith('test_') and file.endswith('.py'):
                filepath = os.path.join(root, file)
                # Try to run just collection on this file
                result = subprocess.run(
                    [sys.executable, '-m', 'pytest', filepath, '--collect-only', '-q'],
                    capture_output=True,
                    text=True,
                    timeout=5
                )
                
                # Check for errors
                if result.returncode != 0:
                    if 'error' in result.stdout.lower() or 'error' in result.stderr.lower():
                        broken_files.append(filepath)
                        print(f"BROKEN: {filepath}")
    
    return broken_files

if __name__ == "__main__":
    print("Finding broken test files...")
    broken = find_broken_tests()
    
    print(f"\n\nFound {len(broken)} broken test files:")
    for f in broken:
        print(f"  - {f}")
    
    # Write to file
    with open("broken_tests.txt", "w") as f:
        f.write("\n".join(broken))
    
    print(f"\nWritten to broken_tests.txt")
