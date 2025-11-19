#!/usr/bin/env python3
"""
Plugin Generator Tool
Automatically generates Windows AI plugins from templates

Usage:
    python scripts/generate_plugin.py api "OpenAI" --key OPENAI_API_KEY --url https://api.openai.com/v1
    python scripts/generate_plugin.py storage "Notion" --key NOTION_API_KEY --url https://api.notion.com
    python scripts/generate_plugin.py local "Ollama" --executable ollama
    python scripts/generate_plugin.py utility "Text Analyzer"
"""

import argparse
import sys
from pathlib import Path
from typing import Dict

# Template directory
SCRIPT_DIR = Path(__file__).parent
TEMPLATE_DIR = SCRIPT_DIR / "templates"
OUTPUT_DIR = SCRIPT_DIR.parent / "windows_ai" / "plugins" / "builtin"

# Templates as strings (embedded for portability)
API_TEMPLATE = '''"""
{PLUGIN_NAME} Plugin
{DESCRIPTION}
"""
from typing import Dict, Any
import os
import logging
import aiohttp

logger = logging.getLogger(__name__)

class Plugin:
    """Plugin for {SERVICE_NAME} integration"""
    
    def __init__(self):
        self.name = "{PLUGIN_NAME}"
        self.version = "1.0.0"
        self.description = "{DESCRIPTION}"
        
        # Configuration
        self.api_key = os.getenv("{API_KEY_ENV_VAR}", "")
        self.base_url = "{API_BASE_URL}"
        self.timeout = 30
    
    async def execute(self, **kwargs) -> Dict[str, Any]:
        """
        Execute {PLUGIN_NAME} request
        
        Args:
            action (str): Action to perform (generate, analyze, etc.)
            **kwargs: Additional parameters
        
        Returns:
            Dict with status and results
        """
        try:
            # Validate API key
            if not self.api_key:
                return {{
                    "status": "error",
                    "message": f"{{self.name}} API key not configured. Set {{self.api_key}} environment variable."
                }}
            
            action = kwargs.get("action", "generate")
            
            # Route to appropriate handler
            if action == "generate":
                return await self._generate(**kwargs)
            elif action == "analyze":
                return await self._analyze(**kwargs)
            elif action == "list":
                return await self._list(**kwargs)
            else:
                return {{"status": "error", "message": f"Unknown action: {{action}}"}}
                
        except Exception as e:
            logger.error(f"{{self.name}} error: {{str(e)}}")
            return {{"status": "error", "message": str(e)}}
    
    async def _generate(self, **kwargs) -> Dict[str, Any]:
        """Generate content using {SERVICE_NAME}"""
        prompt = kwargs.get("prompt", "")
        model = kwargs.get("model", "default")
        max_tokens = kwargs.get("max_tokens", 1000)
        
        async with aiohttp.ClientSession() as session:
            headers = {{
                "Authorization": f"Bearer {{self.api_key}}",
                "Content-Type": "application/json"
            }}
            
            payload = {{
                "model": model,
                "prompt": prompt,
                "max_tokens": max_tokens
            }}
            
            try:
                async with session.post(
                    f"{{self.base_url}}/completions",
                    json=payload,
                    headers=headers,
                    timeout=self.timeout
                ) as response:
                    if response.status == 200:
                        data = await response.json()
                        return {{"status": "success", "result": data}}
                    else:
                        error = await response.text()
                        return {{"status": "error", "message": error, "status_code": response.status}}
            except aiohttp.ClientError as e:
                return {{"status": "error", "message": f"API request failed: {{str(e)}}"}}
    
    async def _analyze(self, **kwargs) -> Dict[str, Any]:
        """Analyze content using {SERVICE_NAME}"""
        text = kwargs.get("text", "")
        
        # Implement analysis logic here
        return {{
            "status": "success",
            "analysis": {{"text_length": len(text)}}
        }}
    
    async def _list(self, **kwargs) -> Dict[str, Any]:
        """List available models/resources"""
        
        async with aiohttp.ClientSession() as session:
            headers = {{"Authorization": f"Bearer {{self.api_key}}"}}
            
            try:
                async with session.get(
                    f"{{self.base_url}}/models",
                    headers=headers,
                    timeout=self.timeout
                ) as response:
                    if response.status == 200:
                        data = await response.json()
                        return {{"status": "success", "models": data}}
                    else:
                        return {{"status": "error", "message": "Failed to list models"}}
            except aiohttp.ClientError as e:
                return {{"status": "error", "message": str(e)}}
'''

STORAGE_TEMPLATE = '''"""
{PLUGIN_NAME} Plugin - Storage/Database integration
{DESCRIPTION}
"""
from typing import Dict, Any, List, Optional
import os
import logging
import aiohttp

logger = logging.getLogger(__name__)

class Plugin:
    """Plugin for {SERVICE_NAME} storage"""
    
    def __init__(self):
        self.name = "{PLUGIN_NAME}"
        self.version = "1.0.0"
        self.description = "{DESCRIPTION}"
        self.api_key = os.getenv("{API_KEY_ENV_VAR}", "")
        self.base_url = "{API_BASE_URL}"
    
    async def execute(self, **kwargs) -> Dict[str, Any]:
        """Execute storage operation"""
        try:
            if not self.api_key:
                return {{"status": "error", "message": "API key not configured"}}
            
            operation = kwargs.get("operation", "list")
            
            if operation == "create":
                return await self._create(**kwargs)
            elif operation == "read":
                return await self._read(**kwargs)
            elif operation == "update":
                return await self._update(**kwargs)
            elif operation == "delete":
                return await self._delete(**kwargs)
            elif operation == "list":
                return await self._list(**kwargs)
            elif operation == "search":
                return await self._search(**kwargs)
            else:
                return {{"status": "error", "message": f"Unknown operation: {{operation}}"}}
                
        except Exception as e:
            logger.error(f"{{self.name}} error: {{str(e)}}")
            return {{"status": "error", "message": str(e)}}
    
    async def _create(self, **kwargs) -> Dict[str, Any]:
        """Create new entry"""
        data = kwargs.get("data", {{}})
        
        async with aiohttp.ClientSession() as session:
            headers = {{"Authorization": f"Bearer {{self.api_key}}", "Content-Type": "application/json"}}
            async with session.post(
                f"{{self.base_url}}/entries",
                json=data,
                headers=headers
            ) as response:
                if response.status in [200, 201]:
                    result = await response.json()
                    return {{"status": "success", "id": result.get("id"), "data": result}}
                else:
                    error = await response.text()
                    return {{"status": "error", "message": error}}
    
    async def _read(self, **kwargs) -> Dict[str, Any]:
        """Read entry by ID"""
        entry_id = kwargs.get("id")
        if not entry_id:
            return {{"status": "error", "message": "No ID provided"}}
        
        async with aiohttp.ClientSession() as session:
            headers = {{"Authorization": f"Bearer {{self.api_key}}"}}
            async with session.get(
                f"{{self.base_url}}/entries/{{entry_id}}",
                headers=headers
            ) as response:
                if response.status == 200:
                    result = await response.json()
                    return {{"status": "success", "data": result}}
                else:
                    return {{"status": "error", "message": "Entry not found"}}
    
    async def _update(self, **kwargs) -> Dict[str, Any]:
        """Update existing entry"""
        entry_id = kwargs.get("id")
        data = kwargs.get("data", {{}})
        
        if not entry_id:
            return {{"status": "error", "message": "No ID provided"}}
        
        async with aiohttp.ClientSession() as session:
            headers = {{"Authorization": f"Bearer {{self.api_key}}", "Content-Type": "application/json"}}
            async with session.patch(
                f"{{self.base_url}}/entries/{{entry_id}}",
                json=data,
                headers=headers
            ) as response:
                if response.status == 200:
                    result = await response.json()
                    return {{"status": "success", "data": result}}
                else:
                    return {{"status": "error", "message": "Update failed"}}
    
    async def _delete(self, **kwargs) -> Dict[str, Any]:
        """Delete entry"""
        entry_id = kwargs.get("id")
        if not entry_id:
            return {{"status": "error", "message": "No ID provided"}}
        
        async with aiohttp.ClientSession() as session:
            headers = {{"Authorization": f"Bearer {{self.api_key}}"}}
            async with session.delete(
                f"{{self.base_url}}/entries/{{entry_id}}",
                headers=headers
            ) as response:
                if response.status in [200, 204]:
                    return {{"status": "success", "message": "Entry deleted"}}
                else:
                    return {{"status": "error", "message": "Delete failed"}}
    
    async def _list(self, **kwargs) -> Dict[str, Any]:
        """List entries with optional filters"""
        limit = kwargs.get("limit", 100)
        offset = kwargs.get("offset", 0)
        
        async with aiohttp.ClientSession() as session:
            headers = {{"Authorization": f"Bearer {{self.api_key}}"}}
            params = {{"limit": limit, "offset": offset}}
            
            async with session.get(
                f"{{self.base_url}}/entries",
                headers=headers,
                params=params
            ) as response:
                if response.status == 200:
                    result = await response.json()
                    return {{"status": "success", "entries": result}}
                else:
                    return {{"status": "error", "message": "List failed"}}
    
    async def _search(self, **kwargs) -> Dict[str, Any]:
        """Search entries"""
        query = kwargs.get("query", "")
        
        async with aiohttp.ClientSession() as session:
            headers = {{"Authorization": f"Bearer {{self.api_key}}"}}
            params = {{"q": query}}
            
            async with session.get(
                f"{{self.base_url}}/search",
                headers=headers,
                params=params
            ) as response:
                if response.status == 200:
                    result = await response.json()
                    return {{"status": "success", "results": result}}
                else:
                    return {{"status": "error", "message": "Search failed"}}
'''

LOCAL_TEMPLATE = '''"""
{PLUGIN_NAME} Plugin - Local Tool Integration
{DESCRIPTION}
"""
from typing import Dict, Any
import logging
import subprocess
import json
import asyncio

logger = logging.getLogger(__name__)

class Plugin:
    """Plugin for {TOOL_NAME} local integration"""
    
    def __init__(self):
        self.name = "{PLUGIN_NAME}"
        self.version = "1.0.0"
        self.description = "{DESCRIPTION}"
        self.executable = "{EXECUTABLE_PATH}"
    
    async def execute(self, **kwargs) -> Dict[str, Any]:
        """Execute local tool command"""
        try:
            # Check if tool is available
            if not await self._is_installed():
                return {{
                    "status": "error",
                    "message": f"{{self.executable}} not found. Please install it first."
                }}
            
            command = kwargs.get("command", "run")
            args = kwargs.get("args", [])
            
            # Build command
            full_command = [self.executable, command] + args
            
            # Execute asynchronously
            process = await asyncio.create_subprocess_exec(
                *full_command,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            
            stdout, stderr = await asyncio.wait_for(
                process.communicate(),
                timeout=kwargs.get("timeout", 60)
            )
            
            if process.returncode == 0:
                output = stdout.decode()
                # Try to parse as JSON
                try:
                    result = json.loads(output)
                    return {{"status": "success", "result": result}}
                except:
                    return {{"status": "success", "output": output}}
            else:
                return {{"status": "error", "message": stderr.decode()}}
                
        except asyncio.TimeoutError:
            return {{"status": "error", "message": "Command timed out"}}
        except Exception as e:
            logger.error(f"{{self.name}} error: {{str(e)}}")
            return {{"status": "error", "message": str(e)}}
    
    async def _is_installed(self) -> bool:
        """Check if tool is installed"""
        try:
            process = await asyncio.create_subprocess_exec(
                self.executable,
                "--version",
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            await asyncio.wait_for(process.communicate(), timeout=5)
            return process.returncode == 0
        except:
            return False
'''

UTILITY_TEMPLATE = '''"""
{PLUGIN_NAME} Plugin - Utility
{DESCRIPTION}
"""
from typing import Dict, Any
import logging

logger = logging.getLogger(__name__)

class Plugin:
    """Utility plugin for {PURPOSE}"""
    
    def __init__(self):
        self.name = "{PLUGIN_NAME}"
        self.version = "1.0.0"
        self.description = "{DESCRIPTION}"
    
    async def execute(self, **kwargs) -> Dict[str, Any]:
        """Execute utility function"""
        try:
            input_data = kwargs.get("input")
            
            if input_data is None:
                return {{"status": "error", "message": "No input provided"}}
            
            # Process the data
            result = await self._process(input_data, **kwargs)
            
            return {{"status": "success", "result": result}}
            
        except Exception as e:
            logger.error(f"{{self.name}} error: {{str(e)}}")
            return {{"status": "error", "message": str(e)}}
    
    async def _process(self, data: Any, **kwargs) -> Any:
        """Process the input data"""
        # TODO: Implement your processing logic here
        # This is just a placeholder
        return {{
            "processed": True,
            "input": str(data),
            "length": len(str(data))
        }}
'''

TEMPLATES = {
    "api": API_TEMPLATE,
    "storage": STORAGE_TEMPLATE,
    "local": LOCAL_TEMPLATE,
    "utility": UTILITY_TEMPLATE
}


def generate_plugin(
    template_type: str,
    plugin_name: str,
    **replacements
) -> Path:
    """
    Generate plugin from template
    
    Args:
        template_type: Type of template (api, storage, local, utility)
        plugin_name: Name of the plugin
        **replacements: Template variable replacements
    
    Returns:
        Path to generated plugin file
    """
    
    # Get template
    if template_type not in TEMPLATES:
        raise ValueError(f"Unknown template type: {template_type}. Choose from: {list(TEMPLATES.keys())}")
    
    template = TEMPLATES[template_type]
    
    # Set defaults
    if "DESCRIPTION" not in replacements:
        replacements["DESCRIPTION"] = f"Integration with {plugin_name}"
    if "SERVICE_NAME" not in replacements:
        replacements["SERVICE_NAME"] = plugin_name
    if "TOOL_NAME" not in replacements:
        replacements["TOOL_NAME"] = plugin_name
    if "PURPOSE" not in replacements:
        replacements["PURPOSE"] = f"{plugin_name} functionality"
    
    # Always set plugin name
    replacements["PLUGIN_NAME"] = plugin_name
    
    # Replace placeholders
    code = template
    for key, value in replacements.items():
        code = code.replace(f"{{{key}}}", value)
    
    # Generate filename
    filename = plugin_name.lower().replace(" ", "_").replace("-", "_") + "_plugin.py"
    output_path = OUTPUT_DIR / filename
    
    # Write file
    output_path.write_text(code)
    
    return output_path


def main():
    parser = argparse.ArgumentParser(
        description="Generate Windows AI plugins from templates",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Generate OpenAI plugin
  python generate_plugin.py api "OpenAI" --key OPENAI_API_KEY --url https://api.openai.com/v1
  
  # Generate Notion plugin
  python generate_plugin.py storage "Notion" --key NOTION_API_KEY --url https://api.notion.com/v1
  
  # Generate Ollama plugin
  python generate_plugin.py local "Ollama" --executable ollama
  
  # Generate utility plugin
  python generate_plugin.py utility "Text Analyzer" --purpose "analyzing text"
        """
    )
    
    parser.add_argument("type", choices=["api", "storage", "local", "utility"], help="Template type")
    parser.add_argument("name", help="Plugin name")
    parser.add_argument("--key", help="API key environment variable name")
    parser.add_argument("--url", help="API base URL")
    parser.add_argument("--executable", help="Executable path/name for local tools")
    parser.add_argument("--purpose", help="Purpose description for utility plugins")
    parser.add_argument("--description", help="Custom description")
    
    args = parser.parse_args()
    
    # Build replacements dict
    replacements = {}
    
    if args.key:
        replacements["API_KEY_ENV_VAR"] = args.key
    if args.url:
        replacements["API_BASE_URL"] = args.url
    if args.executable:
        replacements["EXECUTABLE_PATH"] = args.executable
    if args.purpose:
        replacements["PURPOSE"] = args.purpose
    if args.description:
        replacements["DESCRIPTION"] = args.description
    
    # Generate plugin
    try:
        output_path = generate_plugin(args.type, args.name, **replacements)
        print(f"✅ Generated {args.name} plugin")
        print(f"📁 Location: {output_path}")
        print(f"📝 Next: Edit the plugin to customize specific methods")
    except Exception as e:
        print(f"❌ Error: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
