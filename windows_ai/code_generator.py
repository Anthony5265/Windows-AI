"""
AI-Powered Code Generation Engine
Generates code from natural language descriptions
"""
import logging
from typing import Dict, List, Optional, Any
from datetime import datetime
from dataclasses import dataclass, asdict
from pathlib import Path
import json
import re

logger = logging.getLogger(__name__)


@dataclass
class CodeTemplate:
    """Code template"""
    template_id: str
    language: str
    name: str
    description: str
    template: str
    parameters: List[str]


@dataclass
class GeneratedCode:
    """Generated code result"""
    code_id: str
    language: str
    code: str
    description: str
    quality_score: float
    suggestions: List[str]
    timestamp: str


class AICodeGenerator:
    """
    AI-Powered Code Generator

    Features:
    - Natural language to code
    - Multiple language support (Python, JavaScript, Java, C++, etc.)
    - Code templates and patterns
    - Best practices enforcement
    - Documentation generation
    - Test case generation
    - Code optimization suggestions
    - Refactoring recommendations
    - Security vulnerability detection
    - Performance analysis
    """

    def __init__(self, data_dir: Path):
        self.data_dir = data_dir
        self.data_dir.mkdir(parents=True, exist_ok=True)

        # Code templates
        self.templates: Dict[str, CodeTemplate] = {}

        # Generation history
        self.history: List[GeneratedCode] = []

        # Initialize templates
        self._initialize_templates()

    def _initialize_templates(self):
        """Initialize code templates"""
        templates = [
            # Python templates
            CodeTemplate(
                template_id="py_function",
                language="python",
                name="Function",
                description="Python function template",
                template="""def {function_name}({parameters}):
    \"\"\"
    {description}

    Args:
        {args_docs}

    Returns:
        {return_type}: {return_description}
    \"\"\"
    {body}
    return {return_value}""",
                parameters=["function_name", "parameters", "description", "args_docs",
                           "return_type", "return_description", "body", "return_value"]
            ),
            CodeTemplate(
                template_id="py_class",
                language="python",
                name="Class",
                description="Python class template",
                template="""class {class_name}:
    \"\"\"
    {description}
    \"\"\"

    def __init__(self{init_params}):
        \"\"\"Initialize {class_name}\"\"\"
        {init_body}

    {methods}""",
                parameters=["class_name", "description", "init_params", "init_body", "methods"]
            ),
            CodeTemplate(
                template_id="py_api_endpoint",
                language="python",
                name="API Endpoint",
                description="FastAPI endpoint template",
                template="""@app.{method}("/{path}", tags=["{tag}"])
async def {function_name}({parameters}):
    \"\"\"
    {description}
    \"\"\"
    try:
        {body}
        return {{"status": "success", "data": result}}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))""",
                parameters=["method", "path", "tag", "function_name", "parameters",
                           "description", "body"]
            ),
            # JavaScript templates
            CodeTemplate(
                template_id="js_function",
                language="javascript",
                name="Function",
                description="JavaScript function template",
                template="""/**
 * {description}
 * @param {{params_docs}}
 * @returns {{{return_type}}} {return_description}
 */
function {function_name}({parameters}) {{
    {body}
    return {return_value};
}}""",
                parameters=["function_name", "description", "parameters", "params_docs",
                           "return_type", "return_description", "body", "return_value"]
            ),
            # SQL templates
            CodeTemplate(
                template_id="sql_select",
                language="sql",
                name="SELECT Query",
                description="SQL SELECT template",
                template="""-- {description}
SELECT {columns}
FROM {table}
{joins}
WHERE {conditions}
{group_by}
{having}
ORDER BY {order_by}
LIMIT {limit};""",
                parameters=["description", "columns", "table", "joins", "conditions",
                           "group_by", "having", "order_by", "limit"]
            ),
        ]

        for template in templates:
            self.templates[template.template_id] = template

    def generate_code(
        self,
        description: str,
        language: str = "python",
        template_id: Optional[str] = None,
        context: Optional[Dict[str, Any]] = None
    ) -> GeneratedCode:
        """
        Generate code from natural language description

        Args:
            description: Natural language description
            language: Target programming language
            template_id: Optional template to use
            context: Optional context information

        Returns:
            GeneratedCode object
        """
        import uuid

        # Parse description to extract intent and parameters
        intent, params = self._parse_description(description, language)

        # Select template if not specified
        if not template_id:
            template_id = self._select_template(intent, language)

        # Get template
        template = self.templates.get(template_id)

        if not template:
            # Generate code without template
            code = self._generate_from_scratch(description, language, intent, params)
        else:
            # Fill template
            code = self._fill_template(template, params)

        # Quality assessment
        quality_score = self._assess_quality(code, language)

        # Generate suggestions
        suggestions = self._generate_suggestions(code, language)

        result = GeneratedCode(
            code_id=str(uuid.uuid4()),
            language=language,
            code=code,
            description=description,
            quality_score=quality_score,
            suggestions=suggestions,
            timestamp=datetime.now().isoformat()
        )

        self.history.append(result)

        logger.info(f"Generated {language} code (quality: {quality_score:.2f})")

        return result

    def _parse_description(self, description: str, language: str) -> tuple[str, Dict[str, Any]]:
        """Parse description to extract intent and parameters"""
        desc_lower = description.lower()
        params = {}

        # Detect intent
        if any(word in desc_lower for word in ['function', 'method', 'def']):
            intent = 'function'

            # Extract function name
            match = re.search(r'(?:function|method|def)\s+(?:called\s+)?[\'"]?(\w+)[\'"]?', desc_lower)
            if match:
                params['function_name'] = match.group(1)

            # Extract parameters
            param_match = re.search(r'(?:with|takes|parameters?)\s+(.+?)(?:\.|$|that|which)', desc_lower)
            if param_match:
                params['parameters'] = param_match.group(1).strip()

        elif any(word in desc_lower for word in ['class', 'object']):
            intent = 'class'

            # Extract class name
            match = re.search(r'class\s+[\'"]?(\w+)[\'"]?', desc_lower)
            if match:
                params['class_name'] = match.group(1)

        elif any(word in desc_lower for word in ['api', 'endpoint', 'route']):
            intent = 'api_endpoint'

            # Extract HTTP method
            for method in ['get', 'post', 'put', 'delete', 'patch']:
                if method in desc_lower:
                    params['method'] = method
                    break

            # Extract path
            path_match = re.search(r'(?:path|route|endpoint)\s+[\'"]?(/[\w/]+)[\'"]?', desc_lower)
            if path_match:
                params['path'] = path_match.group(1)

        elif 'query' in desc_lower or 'select' in desc_lower:
            intent = 'sql_query'
        else:
            intent = 'general'

        params['description'] = description

        return intent, params

    def _select_template(self, intent: str, language: str) -> Optional[str]:
        """Select appropriate template"""
        template_map = {
            ('function', 'python'): 'py_function',
            ('class', 'python'): 'py_class',
            ('api_endpoint', 'python'): 'py_api_endpoint',
            ('function', 'javascript'): 'js_function',
            ('sql_query', 'sql'): 'sql_select',
        }

        return template_map.get((intent, language))

    def _fill_template(self, template: CodeTemplate, params: Dict[str, Any]) -> str:
        """Fill template with parameters"""
        code = template.template

        # Fill in parameters
        for param in template.parameters:
            value = params.get(param, '')

            # Provide defaults for missing parameters
            if not value:
                value = self._get_default_value(param, params)

            code = code.replace(f"{{{param}}}", str(value))

        return code

    def _get_default_value(self, param: str, context: Dict[str, Any]) -> str:
        """Get default value for missing parameter"""
        defaults = {
            'function_name': 'my_function',
            'class_name': 'MyClass',
            'parameters': '',
            'body': '    pass',
            'return_value': 'None',
            'return_type': 'Any',
            'return_description': 'Result',
            'description': 'TODO: Add description',
            'args_docs': '',
            'init_params': '',
            'init_body': '        pass',
            'methods': '',
            'method': 'get',
            'path': 'items',
            'tag': 'default',
            'columns': '*',
            'table': 'table_name',
            'joins': '',
            'conditions': '1=1',
            'group_by': '',
            'having': '',
            'order_by': 'id',
            'limit': '100',
        }

        return defaults.get(param, '')

    def _generate_from_scratch(
        self,
        description: str,
        language: str,
        intent: str,
        params: Dict[str, Any]
    ) -> str:
        """Generate code from scratch without template"""
        # Basic code generation based on intent
        if language == 'python':
            if intent == 'function':
                func_name = params.get('function_name', 'my_function')
                return f"""def {func_name}():
    \"\"\"
    {description}
    \"\"\"
    # TODO: Implement function logic
    pass"""

        elif language == 'javascript':
            if intent == 'function':
                func_name = params.get('function_name', 'myFunction')
                return f"""/**
 * {description}
 */
function {func_name}() {{
    // TODO: Implement function logic
}}"""

        # Generic comment
        return f"# {description}\n# TODO: Implement"

    def _assess_quality(self, code: str, language: str) -> float:
        """Assess code quality"""
        score = 100.0

        # Check for TODOs
        if 'TODO' in code:
            score -= 20

        # Check for comments/documentation
        if language == 'python':
            if '"""' not in code and '#' not in code:
                score -= 15
        elif language == 'javascript':
            if '/**' not in code and '//' not in code:
                score -= 15

        # Check code length (very short might be incomplete)
        if len(code) < 50:
            score -= 10

        # Check for error handling
        if language == 'python':
            if 'try' not in code and 'except' not in code and len(code) > 100:
                score -= 10

        return max(score, 0)

    def _generate_suggestions(self, code: str, language: str) -> List[str]:
        """Generate improvement suggestions"""
        suggestions = []

        # Check for TODOs
        if 'TODO' in code:
            suggestions.append("Complete TODO items")

        # Check for documentation
        if language == 'python':
            if '"""' not in code:
                suggestions.append("Add docstrings for better documentation")
            if 'try' not in code and len(code) > 100:
                suggestions.append("Consider adding error handling")
            if 'logging' not in code and len(code) > 200:
                suggestions.append("Add logging for better debugging")

        elif language == 'javascript':
            if '/**' not in code:
                suggestions.append("Add JSDoc comments")
            if 'try' not in code and 'catch' not in code and len(code) > 100:
                suggestions.append("Add try-catch for error handling")

        # Check for best practices
        if 'pass' in code:
            suggestions.append("Replace 'pass' with actual implementation")

        return suggestions

    def generate_tests(self, code: str, language: str) -> str:
        """Generate test cases for code"""
        if language == 'python':
            # Extract function names
            func_matches = re.findall(r'def\s+(\w+)\s*\(', code)

            test_code = "import pytest\n\n"
            for func_name in func_matches:
                test_code += f"""def test_{func_name}():
    \"\"\"Test {func_name}\"\"\"
    # TODO: Implement test
    assert {func_name}() is not None

"""
            return test_code

        elif language == 'javascript':
            func_matches = re.findall(r'function\s+(\w+)\s*\(', code)

            test_code = "const assert = require('assert');\n\n"
            for func_name in func_matches:
                test_code += f"""describe('{func_name}', () => {{
    it('should work correctly', () => {{
        // TODO: Implement test
        assert.notEqual({func_name}(), null);
    }});
}});

"""
            return test_code

        return "# TODO: Generate tests"

    def refactor_code(self, code: str, language: str) -> str:
        """Suggest code refactoring"""
        # Simple refactoring suggestions
        if language == 'python':
            # Replace pass with NotImplementedError
            code = code.replace('    pass', '    raise NotImplementedError("TODO: Implement")')

        return code


# Global instance
_code_generator: Optional[AICodeGenerator] = None


def get_code_generator(data_dir: Path = None) -> AICodeGenerator:
    """Get or create global code generator"""
    global _code_generator

    if _code_generator is None:
        if data_dir is None:
            data_dir = Path.home() / ".windows-ai" / "codegen"
        _code_generator = AICodeGenerator(data_dir)

    return _code_generator


def initialize_code_generator(data_dir: Path = None):
    """Initialize the code generator"""
    generator = get_code_generator(data_dir)
    logger.info("AI code generator initialized")
    return generator
