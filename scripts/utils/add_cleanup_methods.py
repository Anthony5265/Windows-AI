"""
Add cleanup() methods to all integration manager files
"""

import os
import re
from pathlib import Path

INTEGRATIONS_DIR = Path("windows_ai/integrations")

CLEANUP_METHOD = '''
    async def cleanup(self):
        """Cleanup resources before shutdown"""
        try:
            # Close any open connections
            if hasattr(self, '_clients'):
                for client in self._clients.values():
                    if hasattr(client, 'close'):
                        await client.close() if asyncio.iscoroutinefunction(client.close) else client.close()
            
            # Reset initialization flag
            self._initialized = False
            logger.info(f"{self.__class__.__name__} cleanup completed")
            
        except Exception as e:
            logger.error(f"{self.__class__.__name__} cleanup failed: {e}")
'''

def add_cleanup_to_file(file_path: Path):
    """Add cleanup method to a manager file if it doesn't have one"""
    
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Check if cleanup method already exists
    if 'async def cleanup' in content:
        print(f"✓ {file_path.name} already has cleanup()")
        return False
    
    # Find the class definition
    class_match = re.search(r'class (\w+Manager):', content)
    if not class_match:
        print(f"✗ {file_path.name} - No Manager class found")
        return False
    
    class_name = class_match.group(1)
    
    # Find the initialize method
    init_match = re.search(r'(    async def initialize.*?)(?=\n    async def |\n    def |\nclass |\Z)', content, re.DOTALL)
    if not init_match:
        print(f"✗ {file_path.name} - No initialize() method found")
        return False
    
    init_end_pos = init_match.end()
    
    # Insert cleanup method after initialize
    new_content = content[:init_end_pos] + CLEANUP_METHOD + content[init_end_pos:]
    
    # Write back
    with open(file_path, 'w', encoding='utf-8') as f:
        f.write(new_content)
    
    print(f"✓ {file_path.name} - Added cleanup()")
    return True

def main():
    """Add cleanup() to all integration files"""
    
    if not INTEGRATIONS_DIR.exists():
        print(f"Error: {INTEGRATIONS_DIR} not found")
        return
    
    files_modified = 0
    files_skipped = 0
    
    # Process all .py files except __init__.py
    for py_file in INTEGRATIONS_DIR.glob("*.py"):
        if py_file.name == '__init__.py':
            continue
        
        if add_cleanup_to_file(py_file):
            files_modified += 1
        else:
            files_skipped += 1
    
    print(f"\n{'='*60}")
    print(f"Summary:")
    print(f"  Modified: {files_modified} files")
    print(f"  Skipped:  {files_skipped} files")
    print(f"{'='*60}")

if __name__ == "__main__":
    main()
