# Plugin Implementation Templates
**Purpose:** Accelerate plugin development by providing reusable patterns

## What Are Implementation Templates?

Templates are pre-built code patterns for common plugin types. Instead of writing each plugin from scratch, you copy a template and customize it.

---

## Template Types

### 1. API Wrapper Template
**Use for:** OpenAI, Anthropic, Google, any REST API service

```python
"""
{PLUGIN_NAME} Plugin
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
        self.api_key = os.getenv("{API_KEY_ENV_VAR}")
        self.base_url = "{API_BASE_URL}"
        self.timeout = 30
    
    async def execute(self, **kwargs) -> Dict[str, Any]:
        """
        Execute {PLUGIN_NAME} request
        
        Args:
            **kwargs: Plugin-specific parameters
                - action: str - What to do (required)
                - Additional params based on action
        
        Returns:
            Dict with status and results
        """
        try:
            # Validate API key
            if not self.api_key:
                return {
                    "status": "error",
                    "message": f"{self.name} API key not configured. Set {API_KEY_ENV_VAR} environment variable."
                }
            
            action = kwargs.get("action")
            if not action:
                return {"status": "error", "message": "No action specified"}
            
            # Route to appropriate handler
            if action == "generate":
                return await self._generate(**kwargs)
            elif action == "analyze":
                return await self._analyze(**kwargs)
            else:
                return {"status": "error", "message": f"Unknown action: {action}"}
                
        except Exception as e:
            logger.error(f"{self.name} error: {str(e)}")
            return {"status": "error", "message": str(e)}
    
    async def _generate(self, **kwargs) -> Dict[str, Any]:
        """Generate content using {SERVICE_NAME}"""
        prompt = kwargs.get("prompt", "")
        
        async with aiohttp.ClientSession() as session:
            headers = {
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json"
            }
            
            payload = {
                "prompt": prompt,
                "max_tokens": kwargs.get("max_tokens", 1000)
            }
            
            async with session.post(
                f"{self.base_url}/generate",
                json=payload,
                headers=headers,
                timeout=self.timeout
            ) as response:
                if response.status == 200:
                    data = await response.json()
                    return {"status": "success", "result": data}
                else:
                    error = await response.text()
                    return {"status": "error", "message": error}
    
    async def _analyze(self, **kwargs) -> Dict[str, Any]:
        """Analyze content using {SERVICE_NAME}"""
        # Implementation here
        pass
```

**Usage:**
Replace `{PLUGIN_NAME}`, `{SERVICE_NAME}`, `{API_KEY_ENV_VAR}`, `{API_BASE_URL}` with actual values.

---

### 2. Database/Storage Template
**Use for:** Notion, Airtable, Google Sheets, databases

```python
"""
{PLUGIN_NAME} Plugin - Storage/Database integration
"""
from typing import Dict, Any, List
import os
import logging
import aiohttp

logger = logging.getLogger(__name__)

class Plugin:
    """Plugin for {SERVICE_NAME} storage"""
    
    def __init__(self):
        self.name = "{PLUGIN_NAME}"
        self.version = "1.0.0"
        self.api_key = os.getenv("{API_KEY_ENV_VAR}")
        self.base_url = "{API_BASE_URL}"
    
    async def execute(self, **kwargs) -> Dict[str, Any]:
        """Execute storage operation"""
        try:
            if not self.api_key:
                return {"status": "error", "message": "API key not configured"}
            
            operation = kwargs.get("operation")
            
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
            else:
                return {"status": "error", "message": f"Unknown operation: {operation}"}
                
        except Exception as e:
            logger.error(f"{self.name} error: {str(e)}")
            return {"status": "error", "message": str(e)}
    
    async def _create(self, **kwargs) -> Dict[str, Any]:
        """Create new entry"""
        data = kwargs.get("data", {})
        
        async with aiohttp.ClientSession() as session:
            headers = {"Authorization": f"Bearer {self.api_key}"}
            async with session.post(
                f"{self.base_url}/entries",
                json=data,
                headers=headers
            ) as response:
                result = await response.json()
                return {"status": "success", "id": result.get("id"), "data": result}
    
    async def _read(self, **kwargs) -> Dict[str, Any]:
        """Read entry by ID"""
        entry_id = kwargs.get("id")
        
        async with aiohttp.ClientSession() as session:
            headers = {"Authorization": f"Bearer {self.api_key}"}
            async with session.get(
                f"{self.base_url}/entries/{entry_id}",
                headers=headers
            ) as response:
                result = await response.json()
                return {"status": "success", "data": result}
    
    async def _update(self, **kwargs) -> Dict[str, Any]:
        """Update existing entry"""
        # Implementation
        pass
    
    async def _delete(self, **kwargs) -> Dict[str, Any]:
        """Delete entry"""
        # Implementation
        pass
    
    async def _list(self, **kwargs) -> Dict[str, Any]:
        """List entries with optional filters"""
        # Implementation
        pass
```

---

### 3. Simple Utility Template
**Use for:** Text processing, calculations, conversions

```python
"""
{PLUGIN_NAME} Plugin - Utility
"""
from typing import Dict, Any
import logging

logger = logging.getLogger(__name__)

class Plugin:
    """Utility plugin for {PURPOSE}"""
    
    def __init__(self):
        self.name = "{PLUGIN_NAME}"
        self.version = "1.0.0"
    
    async def execute(self, **kwargs) -> Dict[str, Any]:
        """Execute utility function"""
        try:
            input_data = kwargs.get("input")
            
            if not input_data:
                return {"status": "error", "message": "No input provided"}
            
            # Process the data
            result = self._process(input_data)
            
            return {"status": "success", "result": result}
            
        except Exception as e:
            logger.error(f"{self.name} error: {str(e)}")
            return {"status": "error", "message": str(e)}
    
    def _process(self, data: Any) -> Any:
        """Process the input data"""
        # Your logic here
        return data
```

---

### 4. Local Tool Integration Template
**Use for:** Ollama, LM Studio, local services

```python
"""
{PLUGIN_NAME} Plugin - Local Tool Integration
"""
from typing import Dict, Any
import logging
import subprocess
import json

logger = logging.getLogger(__name__)

class Plugin:
    """Plugin for {TOOL_NAME} local integration"""
    
    def __init__(self):
        self.name = "{PLUGIN_NAME}"
        self.version = "1.0.0"
        self.executable = "{EXECUTABLE_PATH}"  # e.g., "ollama"
    
    async def execute(self, **kwargs) -> Dict[str, Any]:
        """Execute local tool command"""
        try:
            # Check if tool is available
            if not self._is_installed():
                return {
                    "status": "error",
                    "message": f"{self.executable} not found. Please install it first."
                }
            
            command = kwargs.get("command")
            args = kwargs.get("args", [])
            
            # Build command
            full_command = [self.executable, command] + args
            
            # Execute
            result = subprocess.run(
                full_command,
                capture_output=True,
                text=True,
                timeout=60
            )
            
            if result.returncode == 0:
                return {"status": "success", "output": result.stdout}
            else:
                return {"status": "error", "message": result.stderr}
                
        except subprocess.TimeoutExpired:
            return {"status": "error", "message": "Command timed out"}
        except Exception as e:
            logger.error(f"{self.name} error: {str(e)}")
            return {"status": "error", "message": str(e)}
    
    def _is_installed(self) -> bool:
        """Check if tool is installed"""
        try:
            subprocess.run(
                [self.executable, "--version"],
                capture_output=True,
                timeout=5
            )
            return True
        except:
            return False
```

---

## Template Generator Script

Create `generate_plugin.py`:

```python
#!/usr/bin/env python3
"""Plugin Generator - Creates plugins from templates"""

import sys
from pathlib import Path

TEMPLATES = {
    "api": "api_wrapper_template.py",
    "storage": "storage_template.py",
    "utility": "utility_template.py",
    "local": "local_tool_template.py"
}

def generate_plugin(template_type: str, plugin_name: str, **replacements):
    """Generate plugin from template"""
    
    template_path = Path(__file__).parent / "templates" / TEMPLATES[template_type]
    template = template_path.read_text()
    
    # Replace placeholders
    for key, value in replacements.items():
        template = template.replace(f"{{{key}}}", value)
    
    # Save to builtin plugins
    output_path = Path(__file__).parent.parent / "windows_ai" / "plugins" / "builtin" / f"{plugin_name.lower().replace(' ', '_')}_plugin.py"
    output_path.write_text(template)
    
    print(f"✅ Generated {plugin_name} plugin at {output_path}")

if __name__ == "__main__":
    # Example: python generate_plugin.py api "OpenAI GPT-4" OPENAI_API_KEY https://api.openai.com/v1
    
    template_type = sys.argv[1]
    plugin_name = sys.argv[2]
    
    if template_type == "api":
        generate_plugin(
            "api",
            plugin_name,
            PLUGIN_NAME=plugin_name,
            SERVICE_NAME=plugin_name,
            API_KEY_ENV_VAR=sys.argv[3],
            API_BASE_URL=sys.argv[4],
            DESCRIPTION=f"Integration with {plugin_name}"
        )
```

---

## Benefits of Templates

1. **Speed:** Generate plugin in 5 minutes vs 30-60 minutes
2. **Consistency:** All plugins follow same patterns
3. **Quality:** Built-in error handling, logging, validation
4. **Maintenance:** Fix template once, affects all generated plugins
5. **Testing:** Template includes test structure

---

## Usage Example

**Without template:** Write OpenAI plugin from scratch (30-60 min)
**With template:** 
```bash
python generate_plugin.py api "OpenAI GPT-4" OPENAI_API_KEY https://api.openai.com/v1
# Edit specific methods: 5 minutes
# Total: 5-10 minutes
```

For 2,487 plugins:
- Without templates: 1,243-2,487 hours (155-311 days)
- With templates: 200-400 hours (25-50 days)

**Time saved: ~80%**

---

## Next Steps

1. Create template files
2. Build generator script
3. Generate Tier 1 critical plugins (50)
4. Test and refine templates
5. Batch generate remaining plugins
