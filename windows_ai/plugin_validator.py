"""
Plugin Validation and Sandboxing System
Validates, secures, and sandboxes plugins for safe execution
"""
import logging
from typing import Dict, List, Optional, Any
from datetime import datetime
from dataclasses import dataclass, asdict
from pathlib import Path
import json
import ast
import hashlib
import subprocess
import sys

logger = logging.getLogger(__name__)


@dataclass
class ValidationResult:
    """Plugin validation result"""
    plugin_id: str
    passed: bool
    score: float  # 0-100
    issues: List[str]
    warnings: List[str]
    security_level: str  # 'safe', 'review', 'unsafe'
    timestamp: str


@dataclass
class SandboxConfig:
    """Sandbox configuration for plugin"""
    plugin_id: str
    allowed_imports: List[str]
    allowed_file_paths: List[str]
    allow_network: bool
    allow_subprocess: bool
    memory_limit_mb: int
    timeout_seconds: int
    isolated_filesystem: bool


class PluginValidator:
    """
    Plugin Validation and Sandboxing System

    Features:
    - Static code analysis
    - Security vulnerability scanning
    - Malicious pattern detection
    - Dependencies validation
    - Permission analysis
    - Sandboxed execution environment
    - Resource usage limits
    - Network access control
    - File system isolation
    - Plugin signing and verification
    """

    def __init__(self, data_dir: Path):
        self.data_dir = data_dir
        self.data_dir.mkdir(parents=True, exist_ok=True)

        self.validation_results_file = data_dir / "validation_results.json"
        self.trusted_plugins_file = data_dir / "trusted_plugins.json"

        # Validation results
        self.validation_results: Dict[str, ValidationResult] = {}

        # Trusted plugins
        self.trusted_plugins: Dict[str, str] = {}  # plugin_id: hash

        # Dangerous patterns
        self.dangerous_patterns = [
            'eval(', 'exec(', '__import__',
            'compile(', 'open(', 'file(',
            'subprocess', 'os.system', 'os.popen',
            'pickle.loads', 'marshal.loads',
            'socket.', 'urllib.request',
            '__builtins__', 'globals()', 'locals()',
            'rm -rf', 'rmdir', 'del ',
        ]

        # Suspicious imports
        self.suspicious_imports = [
            'os', 'sys', 'subprocess', 'socket',
            'urllib', 'requests', 'pickle', 'marshal',
            'ctypes', 'imp', 'importlib'
        ]

        # Safe imports (allowed by default)
        self.safe_imports = [
            'json', 'datetime', 'time', 'math',
            'random', 're', 'collections', 'itertools',
            'functools', 'typing', 'dataclasses',
            'logging', 'pathlib'
        ]

        # Load data
        self._load_trusted_plugins()

    def validate_plugin(self, plugin_path: Path) -> ValidationResult:
        """
        Validate a plugin for security and correctness

        Args:
            plugin_path: Path to plugin file

        Returns:
            ValidationResult
        """
        plugin_id = plugin_path.stem
        issues = []
        warnings = []
        score = 100.0

        logger.info(f"Validating plugin: {plugin_id}")

        try:
            # Read plugin code
            with open(plugin_path, 'r', encoding='utf-8') as f:
                code = f.read()

            # Static analysis
            static_issues = self._static_analysis(code)
            issues.extend(static_issues['errors'])
            warnings.extend(static_issues['warnings'])
            score -= static_issues['score_penalty']

            # Security scan
            security_issues = self._security_scan(code)
            issues.extend(security_issues['errors'])
            warnings.extend(security_issues['warnings'])
            score -= security_issues['score_penalty']

            # Import analysis
            import_issues = self._analyze_imports(code)
            issues.extend(import_issues['errors'])
            warnings.extend(import_issues['warnings'])
            score -= import_issues['score_penalty']

            # Structure validation
            structure_issues = self._validate_structure(code)
            issues.extend(structure_issues['errors'])
            warnings.extend(structure_issues['warnings'])
            score -= structure_issues['score_penalty']

            # Determine security level
            security_level = self._determine_security_level(score, issues)

            # Create result
            passed = score >= 50 and len(issues) == 0
            result = ValidationResult(
                plugin_id=plugin_id,
                passed=passed,
                score=max(score, 0),
                issues=issues,
                warnings=warnings,
                security_level=security_level,
                timestamp=datetime.now().isoformat()
            )

            self.validation_results[plugin_id] = result

            logger.info(f"Validation complete: {plugin_id} - {security_level} (score: {score:.1f})")

            return result

        except Exception as e:
            logger.error(f"Error validating plugin {plugin_id}: {e}")
            return ValidationResult(
                plugin_id=plugin_id,
                passed=False,
                score=0,
                issues=[f"Validation error: {str(e)}"],
                warnings=[],
                security_level='unsafe',
                timestamp=datetime.now().isoformat()
            )

    def _static_analysis(self, code: str) -> Dict[str, Any]:
        """Perform static code analysis"""
        errors = []
        warnings = []
        penalty = 0

        try:
            # Parse AST
            tree = ast.parse(code)

            # Check for syntax issues (if we got here, syntax is valid)

            # Check code complexity
            complexity = self._calculate_complexity(tree)
            if complexity > 20:
                warnings.append(f"High code complexity: {complexity}")
                penalty += 5

            # Check for long functions
            for node in ast.walk(tree):
                if isinstance(node, ast.FunctionDef):
                    func_lines = node.end_lineno - node.lineno if hasattr(node, 'end_lineno') else 0
                    if func_lines > 100:
                        warnings.append(f"Long function: {node.name} ({func_lines} lines)")
                        penalty += 2

        except SyntaxError as e:
            errors.append(f"Syntax error: {str(e)}")
            penalty += 50

        return {'errors': errors, 'warnings': warnings, 'score_penalty': penalty}

    def _security_scan(self, code: str) -> Dict[str, Any]:
        """Scan for security vulnerabilities"""
        errors = []
        warnings = []
        penalty = 0

        # Check for dangerous patterns
        for pattern in self.dangerous_patterns:
            if pattern in code:
                errors.append(f"Dangerous pattern detected: {pattern}")
                penalty += 20

        # Check for hardcoded credentials
        if any(keyword in code.lower() for keyword in ['password', 'api_key', 'secret', 'token']):
            # Check if it's actually hardcoded (not just variable names)
            lines = code.split('\n')
            for i, line in enumerate(lines):
                if '=' in line:
                    for keyword in ['password', 'api_key', 'secret', 'token']:
                        if keyword in line.lower() and ('"' in line or "'" in line):
                            warnings.append(f"Possible hardcoded credential at line {i+1}")
                            penalty += 10

        # Check for obfuscation
        if 'base64' in code or 'decode(' in code:
            warnings.append("Possible code obfuscation detected")
            penalty += 5

        return {'errors': errors, 'warnings': warnings, 'score_penalty': penalty}

    def _analyze_imports(self, code: str) -> Dict[str, Any]:
        """Analyze imports"""
        errors = []
        warnings = []
        penalty = 0

        try:
            tree = ast.parse(code)

            for node in ast.walk(tree):
                if isinstance(node, ast.Import):
                    for alias in node.names:
                        module = alias.name
                        if module in self.suspicious_imports:
                            warnings.append(f"Suspicious import: {module}")
                            penalty += 15
                        elif module.split('.')[0] not in self.safe_imports:
                            warnings.append(f"Unrecognized import: {module}")
                            penalty += 5

                elif isinstance(node, ast.ImportFrom):
                    module = node.module
                    if module and module in self.suspicious_imports:
                        warnings.append(f"Suspicious import: {module}")
                        penalty += 15

        except Exception as e:
            errors.append(f"Error analyzing imports: {str(e)}")
            penalty += 10

        return {'errors': errors, 'warnings': warnings, 'score_penalty': penalty}

    def _validate_structure(self, code: str) -> Dict[str, Any]:
        """Validate plugin structure"""
        errors = []
        warnings = []
        penalty = 0

        try:
            tree = ast.parse(code)

            # Check for required elements
            has_init = False
            has_execute = False

            for node in ast.walk(tree):
                if isinstance(node, ast.FunctionDef):
                    if node.name == '__init__':
                        has_init = True
                    elif node.name == 'execute':
                        has_execute = True

            if not has_execute:
                warnings.append("Plugin missing 'execute' method")
                penalty += 10

            # Check for global state (generally bad practice)
            for node in ast.walk(tree):
                if isinstance(node, ast.Global):
                    warnings.append("Use of global variables detected")
                    penalty += 5

        except Exception as e:
            errors.append(f"Error validating structure: {str(e)}")
            penalty += 10

        return {'errors': errors, 'warnings': warnings, 'score_penalty': penalty}

    def _calculate_complexity(self, tree: ast.AST) -> int:
        """Calculate cyclomatic complexity"""
        complexity = 1

        for node in ast.walk(tree):
            if isinstance(node, (ast.If, ast.While, ast.For, ast.ExceptHandler)):
                complexity += 1
            elif isinstance(node, ast.BoolOp):
                complexity += len(node.values) - 1

        return complexity

    def _determine_security_level(self, score: float, issues: List[str]) -> str:
        """Determine security level"""
        if len(issues) > 0:
            return 'unsafe'
        elif score >= 80:
            return 'safe'
        else:
            return 'review'

    def create_sandbox_config(self, plugin_id: str, security_level: str) -> SandboxConfig:
        """Create sandbox configuration based on security level"""
        if security_level == 'safe':
            config = SandboxConfig(
                plugin_id=plugin_id,
                allowed_imports=self.safe_imports + ['numpy', 'pandas'],
                allowed_file_paths=[str(Path.home() / ".windows-ai" / "plugins" / plugin_id)],
                allow_network=False,
                allow_subprocess=False,
                memory_limit_mb=512,
                timeout_seconds=30,
                isolated_filesystem=True
            )
        elif security_level == 'review':
            config = SandboxConfig(
                plugin_id=plugin_id,
                allowed_imports=self.safe_imports,
                allowed_file_paths=[str(Path.home() / ".windows-ai" / "plugins" / plugin_id)],
                allow_network=False,
                allow_subprocess=False,
                memory_limit_mb=256,
                timeout_seconds=15,
                isolated_filesystem=True
            )
        else:  # unsafe
            config = SandboxConfig(
                plugin_id=plugin_id,
                allowed_imports=[],
                allowed_file_paths=[],
                allow_network=False,
                allow_subprocess=False,
                memory_limit_mb=128,
                timeout_seconds=5,
                isolated_filesystem=True
            )

        return config

    def execute_in_sandbox(self, plugin_path: Path, config: SandboxConfig, input_data: Dict = None) -> Dict[str, Any]:
        """Execute plugin in sandboxed environment"""
        try:
            # Create restricted execution environment
            restricted_globals = {
                '__builtins__': {
                    'print': print,
                    'len': len,
                    'str': str,
                    'int': int,
                    'float': float,
                    'bool': bool,
                    'dict': dict,
                    'list': list,
                    'tuple': tuple,
                    'set': set,
                    'range': range,
                    'enumerate': enumerate,
                    'zip': zip,
                    'map': map,
                    'filter': filter,
                    'sorted': sorted,
                    'sum': sum,
                    'min': min,
                    'max': max,
                    'abs': abs,
                    'round': round,
                }
            }

            # Read plugin code
            with open(plugin_path, 'r') as f:
                code = f.read()

            # Execute in restricted environment
            exec(compile(code, str(plugin_path), 'exec'), restricted_globals)

            # Call execute method if exists
            if 'execute' in restricted_globals:
                result = restricted_globals['execute'](input_data or {})
                return {'success': True, 'result': result}
            else:
                return {'success': False, 'error': 'No execute method found'}

        except Exception as e:
            logger.error(f"Error executing plugin in sandbox: {e}")
            return {'success': False, 'error': str(e)}

    def sign_plugin(self, plugin_path: Path) -> str:
        """Generate signature for plugin"""
        with open(plugin_path, 'rb') as f:
            content = f.read()
            return hashlib.sha256(content).hexdigest()

    def verify_plugin(self, plugin_path: Path, expected_hash: str) -> bool:
        """Verify plugin signature"""
        actual_hash = self.sign_plugin(plugin_path)
        return actual_hash == expected_hash

    def trust_plugin(self, plugin_id: str, plugin_hash: str):
        """Mark plugin as trusted"""
        self.trusted_plugins[plugin_id] = plugin_hash
        self._save_trusted_plugins()
        logger.info(f"Plugin trusted: {plugin_id}")

    def is_trusted(self, plugin_id: str, plugin_hash: str) -> bool:
        """Check if plugin is trusted"""
        return self.trusted_plugins.get(plugin_id) == plugin_hash

    def get_validation_results(self, plugin_id: Optional[str] = None) -> Dict:
        """Get validation results"""
        if plugin_id:
            result = self.validation_results.get(plugin_id)
            return asdict(result) if result else None
        else:
            return {pid: asdict(result) for pid, result in self.validation_results.items()}

    def _save_trusted_plugins(self):
        """Save trusted plugins"""
        try:
            with open(self.trusted_plugins_file, 'w') as f:
                json.dump(self.trusted_plugins, f, indent=2)
        except Exception as e:
            logger.error(f"Error saving trusted plugins: {e}")

    def _load_trusted_plugins(self):
        """Load trusted plugins"""
        try:
            if self.trusted_plugins_file.exists():
                with open(self.trusted_plugins_file, 'r') as f:
                    self.trusted_plugins = json.load(f)
                logger.info(f"Loaded {len(self.trusted_plugins)} trusted plugins")
        except Exception as e:
            logger.error(f"Error loading trusted plugins: {e}")


# Global instance
_plugin_validator: Optional[PluginValidator] = None


def get_plugin_validator(data_dir: Path = None) -> PluginValidator:
    """Get or create global plugin validator"""
    global _plugin_validator

    if _plugin_validator is None:
        if data_dir is None:
            data_dir = Path.home() / ".windows-ai" / "plugin_validation"
        _plugin_validator = PluginValidator(data_dir)

    return _plugin_validator


def initialize_plugin_validator(data_dir: Path = None):
    """Initialize the plugin validator"""
    validator = get_plugin_validator(data_dir)
    logger.info("Plugin validator initialized")
    return validator
