#!/usr/bin/env python3
"""Analyze imports in GUI modules to identify issues."""

import os
import re

gui_files = [
    'windows_ai/gui/__init__.py',
    'windows_ai/gui/main_window.py', 
    'windows_ai/gui/gui/__init__.py',
    'windows_ai/gui/gui/core.py',
    'windows_ai/gui/gui/simple_model.py'
]

import_pattern = re.compile(r'^\s*(from\s+\S+\s+)?import\s+')

for filepath in gui_files:
    if os.path.exists(filepath):
        try:
            with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
                lines = f.readlines()[:100]
                print(f'\n{"="*70}')
                print(f'FILE: {filepath}')
                print(f'{"="*70}')
                
                imports = []
                for i, line in enumerate(lines, 1):
                    if import_pattern.match(line):
                        imports.append((i, line.rstrip()))
                        
                if imports:
                    for line_num, import_line in imports:
                        print(f'{line_num:3}: {import_line}')
                else:
                    print("No imports found in first 100 lines")
                    
        except Exception as e:
            print(f'Error reading {filepath}: {e}')
    else:
        print(f'\nFile not found: {filepath}')

print(f'\n{"="*70}')
print("Import Analysis Complete")
print(f'{"="*70}')
