"""
Import Fixer Agent
Automatically detects and fixes import errors, circular dependencies, broken imports
"""

import ast
import logging
from pathlib import Path
from typing import Dict, List, Set, Tuple, Optional
import importlib.util
import sys

logger = logging.getLogger(__name__)


class ImportFixerAgent:
    """
    Agent that fixes import errors automatically
    
    Features:
    - Detects missing __init__.py exports
    - Finds circular dependencies
    - Auto-generates proper __init__.py files
    - Fixes broken import paths
    - Creates compatibility shims
    """
    
    def __init__(self, project_root: str):
        self.project_root = Path(project_root)
        self.module_exports: Dict[str, Set[str]] = {}
        self.import_graph: Dict[str, Set[str]] = {}
        self.errors: List[Dict] = []
    
    def scan_for_import_errors(self, directory: str = None) -> List[Dict]:
        """
        Scan for import errors in directory
        
        Args:
            directory: Directory to scan (defaults to project root)
        
        Returns:
            List of import errors found
        """
        scan_dir = Path(directory) if directory else self.project_root
        errors = []
        
        for py_file in scan_dir.rglob("*.py"):
            if "__pycache__" in str(py_file):
                continue
            
            file_errors = self._check_file_imports(py_file)
            errors.extend(file_errors)
        
        self.errors = errors
        return errors
    
    def _check_file_imports(self, file_path: Path) -> List[Dict]:
        """Check imports in a single file"""
        errors = []
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                source = f.read()
            
            tree = ast.parse(source)
            
            for node in ast.walk(tree):
                if isinstance(node, ast.Import):
                    for alias in node.names:
                        if not self._can_import(alias.name):
                            errors.append({
                                "file": str(file_path),
                                "line": node.lineno,
                                "type": "missing_module",
                                "module": alias.name,
                                "statement": ast.unparse(node)
                            })
                
                elif isinstance(node, ast.ImportFrom):
                    module = node.module or ""
                    for alias in node.names:
                        if not self._can_import_from(module, alias.name):
                            errors.append({
                                "file": str(file_path),
                                "line": node.lineno,
                                "type": "missing_import",
                                "module": module,
                                "name": alias.name,
                                "statement": ast.unparse(node)
                            })
        
        except SyntaxError as e:
            errors.append({
                "file": str(file_path),
                "line": e.lineno,
                "type": "syntax_error",
                "error": str(e)
            })
        except Exception as e:
            logger.error(f"Failed to check {file_path}: {e}")
        
        return errors
    
    def _can_import(self, module_name: str) -> bool:
        """Check if a module can be imported"""
        try:
            spec = importlib.util.find_spec(module_name)
            return spec is not None
        except (ImportError, ModuleNotFoundError, ValueError):
            return False
    
    def _can_import_from(self, module: str, name: str) -> bool:
        """Check if can import name from module"""
        try:
            spec = importlib.util.find_spec(module)
            if not spec or not spec.origin:
                return False
            
            # Check if name is exported in __init__.py
            if spec.origin.endswith("__init__.py"):
                exports = self._get_module_exports(spec.origin)
                return name in exports or name == "*"
            
            return True
        except (ImportError, ModuleNotFoundError, ValueError):
            return False
    
    def _get_module_exports(self, init_file: str) -> Set[str]:
        """Get what a module exports from its __init__.py"""
        if init_file in self.module_exports:
            return self.module_exports[init_file]
        
        exports = set()
        
        try:
            with open(init_file, 'r', encoding='utf-8') as f:
                source = f.read()
            
            tree = ast.parse(source)
            
            # Check for __all__
            for node in ast.walk(tree):
                if isinstance(node, ast.Assign):
                    for target in node.targets:
                        if isinstance(target, ast.Name) and target.id == "__all__":
                            if isinstance(node.value, (ast.List, ast.Tuple)):
                                for elt in node.value.elts:
                                    if isinstance(elt, ast.Constant):
                                        exports.add(elt.value)
                
                # Also track explicit imports
                elif isinstance(node, ast.ImportFrom):
                    for alias in node.names:
                        exports.add(alias.asname or alias.name)
            
            self.module_exports[init_file] = exports
            
        except Exception as e:
            logger.error(f"Failed to get exports from {init_file}: {e}")
        
        return exports
    
    def fix_init_exports(self, package_dir: str) -> None:
        """
        Auto-generate/fix __init__.py to export all public classes/functions
        
        Args:
            package_dir: Directory containing Python package
        """
        pkg_path = Path(package_dir)
        init_file = pkg_path / "__init__.py"
        
        # Scan all .py files in package
        exports = set()
        imports = []
        
        for py_file in pkg_path.glob("*.py"):
            if py_file.name == "__init__.py":
                continue
            
            module_name = py_file.stem
            
            # Parse file to find public classes and functions
            try:
                with open(py_file, 'r', encoding='utf-8') as f:
                    tree = ast.parse(f.read())
                
                for node in ast.walk(tree):
                    if isinstance(node, ast.ClassDef):
                        if not node.name.startswith("_"):
                            exports.add(node.name)
                            imports.append(f"from .{module_name} import {node.name}")
                    
                    elif isinstance(node, ast.FunctionDef):
                        if not node.name.startswith("_"):
                            exports.add(node.name)
                            imports.append(f"from .{module_name} import {node.name}")
            
            except Exception as e:
                logger.error(f"Failed to parse {py_file}: {e}")
        
        if not exports:
            return
        
        # Generate __init__.py content
        content = f'''"""
{pkg_path.name} package
Auto-generated exports by Import Fixer Agent
"""

{chr(10).join(sorted(set(imports)))}

__all__ = [
{chr(10).join(f'    "{name}",' for name in sorted(exports))}
]
'''
        
        # Write __init__.py
        init_file.write_text(content, encoding='utf-8')
        logger.info(f"Generated {init_file} with {len(exports)} exports")
    
    def create_compatibility_shim(self, old_path: str, new_path: str, exports: List[str]) -> None:
        """
        Create compatibility shim for moved modules
        
        Args:
            old_path: Old import path
            new_path: New import path
            exports: What to re-export
        """
        # Convert import path to file path
        old_file = self.project_root / old_path.replace(".", "/")
        old_file = old_file.with_suffix(".py")
        
        # Create parent directories
        old_file.parent.mkdir(parents=True, exist_ok=True)
        
        # Generate shim content
        export_list = ", ".join(exports)
        content = f'''"""
Compatibility shim
Re-exports from {new_path} for backwards compatibility
"""

from {new_path} import {export_list}

__all__ = [{", ".join(f'"{e}"' for e in exports)}]
'''
        
        old_file.write_text(content, encoding='utf-8')
        logger.info(f"Created compatibility shim at {old_file}")
    
    def detect_circular_imports(self) -> List[List[str]]:
        """
        Detect circular import dependencies
        
        Returns:
            List of circular dependency chains
        """
        # Build import graph
        self._build_import_graph()
        
        # Find cycles using DFS
        cycles = []
        visited = set()
        rec_stack = set()
        
        def dfs(node: str, path: List[str]) -> None:
            visited.add(node)
            rec_stack.add(node)
            path.append(node)
            
            for neighbor in self.import_graph.get(node, set()):
                if neighbor not in visited:
                    dfs(neighbor, path.copy())
                elif neighbor in rec_stack:
                    # Found cycle
                    cycle_start = path.index(neighbor)
                    cycle = path[cycle_start:] + [neighbor]
                    cycles.append(cycle)
            
            rec_stack.remove(node)
        
        for node in self.import_graph:
            if node not in visited:
                dfs(node, [])
        
        return cycles
    
    def _build_import_graph(self) -> None:
        """Build graph of module dependencies"""
        self.import_graph.clear()
        
        for py_file in self.project_root.rglob("*.py"):
            if "__pycache__" in str(py_file):
                continue
            
            module_path = str(py_file.relative_to(self.project_root))
            self.import_graph[module_path] = set()
            
            try:
                with open(py_file, 'r', encoding='utf-8') as f:
                    tree = ast.parse(f.read())
                
                for node in ast.walk(tree):
                    if isinstance(node, ast.ImportFrom):
                        if node.module and node.module.startswith("windows_ai"):
                            # Convert module to file path
                            imported_path = node.module.replace(".", "/") + ".py"
                            self.import_graph[module_path].add(imported_path)
            
            except Exception as e:
                logger.error(f"Failed to parse {py_file}: {e}")
    
    def fix_all_imports(self, dry_run: bool = True) -> Dict[str, Any]:
        """
        Find and fix all import errors
        
        Args:
            dry_run: If True, don't modify files
        
        Returns:
            Summary of fixes applied
        """
        summary = {
            "errors_found": 0,
            "fixes_applied": 0,
            "shims_created": 0,
            "init_files_generated": 0
        }
        
        # Scan for errors
        errors = self.scan_for_import_errors()
        summary["errors_found"] = len(errors)
        
        # Group errors by package
        package_errors: Dict[str, List] = {}
        for error in errors:
            if error["type"] == "missing_import":
                pkg = Path(error["file"]).parent
                if pkg not in package_errors:
                    package_errors[pkg] = []
                package_errors[pkg].append(error)
        
        # Fix each package's __init__.py
        for pkg, pkg_errors in package_errors.items():
            if not dry_run:
                self.fix_init_exports(str(pkg))
                summary["init_files_generated"] += 1
        
        # Detect circular imports
        cycles = self.detect_circular_imports()
        if cycles:
            logger.warning(f"Found {len(cycles)} circular import chains:")
            for cycle in cycles:
                logger.warning(" -> ".join(cycle))
        
        return summary


# Agent Interface
async def fix_imports_in_project(project_root: str, dry_run: bool = False) -> Dict:
    """
    Agent method: Fix all import errors in project
    
    Args:
        project_root: Root directory of project
        dry_run: If True, don't modify files
    
    Returns:
        Summary of fixes
    """
    agent = ImportFixerAgent(project_root)
    return agent.fix_all_imports(dry_run=dry_run)


async def generate_init_file(package_dir: str) -> None:
    """
    Agent method: Generate __init__.py for package
    
    Args:
        package_dir: Package directory
    """
    agent = ImportFixerAgent(str(Path(package_dir).parent))
    agent.fix_init_exports(package_dir)


if __name__ == "__main__":
    # Example usage
    agent = ImportFixerAgent("c:/Users/antho/Windows-AI")
    
    # Scan for errors
    errors = agent.scan_for_import_errors()
    print(f"Found {len(errors)} import errors")
    
    # Fix imports (dry run)
    summary = agent.fix_all_imports(dry_run=True)
    print(f"Summary: {summary}")
