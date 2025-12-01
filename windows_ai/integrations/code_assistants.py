"""
Code Assistants Manager
AI code generation and assistance
"""

import asyncio
import logging
import os
from typing import Dict, List, Any, Optional

logger = logging.getLogger(__name__)

class CodeAssistantsManager:
    """AI-powered code assistance"""

    def __init__(self):
        self._initialized = False

    async def initialize(self, config: Optional[Dict] = None):
        if self._initialized:
            return
        self._initialized = True

    async def generate_code(
        self,
        prompt: str,
        language: str = "python",
        provider: str = "openai",
        **kwargs
    ) -> str:
        """Generate code from description"""
        from windows_ai.integrations.ai_providers import AIProvidersManager, Provider

        ai = AIProvidersManager()
        await ai.initialize()

        model = kwargs.get("model")
        if provider == "openai" and not model:
            model = "gpt-4o"
        elif provider == "anthropic" and not model:
            model = "claude-3-5-sonnet-20241022"

        messages = [
            {"role": "system", "content": f"You are an expert {language} programmer. Generate clean, well-documented code. Return ONLY the code, no explanations."},
            {"role": "user", "content": prompt}
        ]

        p = Provider(provider)
        response = await ai.chat(p, messages, model=model)

        code = response["content"]
        if code.startswith("```"):
            lines = code.split("\n")
            code = "\n".join(lines[1:-1])

        return code

    async def explain_code(
        self,
        code: str,
        provider: str = "openai",
        **kwargs
    ) -> str:
        """Explain code"""
        from windows_ai.integrations.ai_providers import AIProvidersManager, Provider

        ai = AIProvidersManager()
        await ai.initialize()

        messages = [
            {"role": "system", "content": "You are a code explainer. Explain the code clearly and concisely."},
            {"role": "user", "content": f"Explain this code:\n\n```\n{code}\n```"}
        ]

        p = Provider(provider)
        response = await ai.chat(p, messages)
        return response["content"]

    async def refactor_code(
        self,
        code: str,
        instructions: str = "Improve code quality and readability",
        provider: str = "openai",
        **kwargs
    ) -> str:
        """Refactor code"""
        from windows_ai.integrations.ai_providers import AIProvidersManager, Provider

        ai = AIProvidersManager()
        await ai.initialize()

        messages = [
            {"role": "system", "content": "You are an expert code refactorer. Return ONLY the refactored code."},
            {"role": "user", "content": f"Refactor this code according to: {instructions}\n\n```\n{code}\n```"}
        ]

        p = Provider(provider)
        response = await ai.chat(p, messages)

        result = response["content"]
        if result.startswith("```"):
            lines = result.split("\n")
            result = "\n".join(lines[1:-1])

        return result

    async def fix_bugs(
        self,
        code: str,
        error: str = None,
        provider: str = "openai",
        **kwargs
    ) -> Dict[str, str]:
        """Fix bugs in code"""
        from windows_ai.integrations.ai_providers import AIProvidersManager, Provider

        ai = AIProvidersManager()
        await ai.initialize()

        error_context = f"\n\nError message:\n{error}" if error else ""

        messages = [
            {"role": "system", "content": "You are a debugging expert. Fix the bug and explain what was wrong."},
            {"role": "user", "content": f"Fix this code:{error_context}\n\n```\n{code}\n```"}
        ]

        p = Provider(provider)
        response = await ai.chat(p, messages)

        return {
            "response": response["content"],
            "provider": provider
        }

    async def generate_tests(
        self,
        code: str,
        framework: str = "pytest",
        provider: str = "openai",
        **kwargs
    ) -> str:
        """Generate tests for code"""
        from windows_ai.integrations.ai_providers import AIProvidersManager, Provider

        ai = AIProvidersManager()
        await ai.initialize()

        messages = [
            {"role": "system", "content": f"You are a testing expert. Generate comprehensive {framework} tests. Return ONLY test code."},
            {"role": "user", "content": f"Generate tests for:\n\n```\n{code}\n```"}
        ]

        p = Provider(provider)
        response = await ai.chat(p, messages)

        result = response["content"]
        if result.startswith("```"):
            lines = result.split("\n")
            result = "\n".join(lines[1:-1])

        return result

    async def generate_documentation(
        self,
        code: str,
        style: str = "docstring",
        provider: str = "openai",
        **kwargs
    ) -> str:
        """Generate documentation for code"""
        from windows_ai.integrations.ai_providers import AIProvidersManager, Provider

        ai = AIProvidersManager()
        await ai.initialize()

        messages = [
            {"role": "system", "content": f"You are a documentation expert. Generate {style} documentation for the code. Return code with documentation added."},
            {"role": "user", "content": f"Add documentation to:\n\n```\n{code}\n```"}
        ]

        p = Provider(provider)
        response = await ai.chat(p, messages)

        result = response["content"]
        if result.startswith("```"):
            lines = result.split("\n")
            result = "\n".join(lines[1:-1])

        return result

    async def code_review(
        self,
        code: str,
        provider: str = "openai",
        **kwargs
    ) -> Dict[str, Any]:
        """Review code for issues and improvements"""
        from windows_ai.integrations.ai_providers import AIProvidersManager, Provider

        ai = AIProvidersManager()
        await ai.initialize()

        messages = [
            {"role": "system", "content": """You are a senior code reviewer. Review the code and provide:
1. Issues found (bugs, security, performance)
2. Suggestions for improvement
3. Code quality score (1-10)
4. Overall assessment"""},
            {"role": "user", "content": f"Review this code:\n\n```\n{code}\n```"}
        ]

        p = Provider(provider)
        response = await ai.chat(p, messages)

        return {
            "review": response["content"],
            "provider": provider
        }

    async def convert_language(
        self,
        code: str,
        from_lang: str,
        to_lang: str,
        provider: str = "openai",
        **kwargs
    ) -> str:
        """Convert code between languages"""
        from windows_ai.integrations.ai_providers import AIProvidersManager, Provider

        ai = AIProvidersManager()
        await ai.initialize()

        messages = [
            {"role": "system", "content": f"You are a polyglot programmer. Convert {from_lang} code to {to_lang}. Return ONLY the converted code."},
            {"role": "user", "content": f"Convert to {to_lang}:\n\n```{from_lang}\n{code}\n```"}
        ]

        p = Provider(provider)
        response = await ai.chat(p, messages)

        result = response["content"]
        if result.startswith("```"):
            lines = result.split("\n")
            result = "\n".join(lines[1:-1])

        return result
