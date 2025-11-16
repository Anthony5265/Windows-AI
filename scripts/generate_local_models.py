#!/usr/bin/env python3
"""
Local Model Platform Plugin Generator
Creates plugins for local AI model platforms
"""

from pathlib import Path
import json


class LocalModelGenerator:
    def __init__(self, repo_root: Path):
        self.repo_root = repo_root
        self.plugins_dir = repo_root / "plugins" / "local_models"
        self.plugins_dir.mkdir(parents=True, exist_ok=True)
    
    def generate_local_platform(self, name: str, executable: str, 
                                default_port: int, models_dir: str):
        """Generate local model platform plugin"""
        
        platform_dir = self.plugins_dir / name.lower().replace(" ", "_")
        platform_dir.mkdir(exist_ok=True)
        
        # __init__.py
        init_content = f'''"""
{name} Local Model Platform Plugin
"""

from .platform import {name.replace(" ", "").replace("-", "")}Platform

__version__ = "1.0.0"
__all__ = ["{name.replace(" ", "").replace("-", "")}Platform"]
'''
        (platform_dir / "__init__.py").write_text(init_content, encoding='utf-8')
        
        # Main platform file
        platform_content = f'''"""
{name} Platform Implementation
Local model inference platform
"""

import subprocess
import requests
import time
from pathlib import Path
from typing import List, Dict, Optional, Any
import json


class {name.replace(" ", "").replace("-", "")}Platform:
    """
    {name} Local Model Platform
    
    Manages local model inference without cloud dependencies
    """
    
    def __init__(self, models_dir: Optional[str] = None, port: int = {default_port}):
        """
        Initialize {name} platform
        
        Args:
            models_dir: Directory containing models (default: {models_dir})
            port: Port for local server (default: {default_port})
        """
        self.models_dir = Path(models_dir or "{models_dir}").expanduser()
        self.port = port
        self.base_url = f"http://localhost:{{port}}"
        self.process = None
        self.executable = "{executable}"
    
    def is_installed(self) -> bool:
        """Check if {name} is installed"""
        try:
            result = subprocess.run(
                [self.executable, "--version"],
                capture_output=True,
                text=True,
                timeout=5
            )
            return result.returncode == 0
        except (FileNotFoundError, subprocess.TimeoutExpired):
            return False
    
    def install(self) -> bool:
        """Install {name} platform"""
        print(f"Installing {name}...")
        try:
            # Platform-specific installation
            if "{name.lower()}" == "ollama":
                # Download and run Ollama installer
                import urllib.request
                import platform
                
                system = platform.system()
                if system == "Windows":
                    url = "https://ollama.ai/download/OllamaSetup.exe"
                    installer = Path.home() / "Downloads" / "OllamaSetup.exe"
                    urllib.request.urlretrieve(url, installer)
                    subprocess.run([str(installer)])
                elif system == "Darwin":  # macOS
                    subprocess.run(["brew", "install", "ollama"])
                else:  # Linux
                    subprocess.run(["curl", "https://ollama.ai/install.sh", "|", "sh"], shell=True)
                
                return True
            else:
                print(f"Please install {name} manually from official website")
                return False
        except Exception as e:
            print(f"Installation failed: {{e}}")
            return False
    
    def start_server(self, background: bool = True) -> bool:
        """Start local model server"""
        if not self.is_installed():
            print(f"{{self.executable}} not found. Installing...")
            if not self.install():
                return False
        
        try:
            # Start server process
            if background:
                self.process = subprocess.Popen(
                    [self.executable, "serve"],
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE
                )
                
                # Wait for server to be ready
                time.sleep(2)
                
                # Check if server is running
                try:
                    requests.get(f"{{self.base_url}}/api/tags", timeout=5)
                    print(f"✅ {name} server started on port {{self.port}}")
                    return True
                except requests.exceptions.RequestException:
                    print(f"❌ Server failed to start")
                    return False
            else:
                subprocess.run([self.executable, "serve"])
                return True
                
        except Exception as e:
            print(f"Failed to start server: {{e}}")
            return False
    
    def stop_server(self):
        """Stop local model server"""
        if self.process:
            self.process.terminate()
            self.process.wait()
            print(f"✅ {name} server stopped")
    
    def list_models(self) -> List[str]:
        """List locally available models"""
        try:
            response = requests.get(f"{{self.base_url}}/api/tags")
            response.raise_for_status()
            data = response.json()
            return [model["name"] for model in data.get("models", [])]
        except requests.exceptions.RequestException:
            return []
    
    def pull_model(self, model_name: str) -> bool:
        """Download a model"""
        try:
            print(f"Downloading {{model_name}}...")
            response = requests.post(
                f"{{self.base_url}}/api/pull",
                json={{"name": model_name}},
                stream=True
            )
            
            for line in response.iter_lines():
                if line:
                    status = json.loads(line)
                    if "status" in status:
                        print(f"  {{status['status']}}")
            
            print(f"✅ Downloaded {{model_name}}")
            return True
            
        except Exception as e:
            print(f"❌ Failed to download {{model_name}}: {{e}}")
            return False
    
    def generate(self, prompt: str, model: str, **kwargs) -> Dict[str, Any]:
        """Generate completion"""
        try:
            payload = {{
                "model": model,
                "prompt": prompt,
                **kwargs
            }}
            
            response = requests.post(
                f"{{self.base_url}}/api/generate",
                json=payload,
                timeout=120
            )
            response.raise_for_status()
            
            result = response.json()
            
            return {{
                "text": result.get("response", ""),
                "model": model,
                "platform": "{name}",
                "local": True
            }}
            
        except requests.exceptions.RequestException as e:
            return {{
                "error": str(e),
                "model": model,
                "platform": "{name}"
            }}
    
    def chat(self, messages: List[Dict[str, str]], model: str, **kwargs) -> Dict[str, Any]:
        """Chat completion"""
        try:
            payload = {{
                "model": model,
                "messages": messages,
                **kwargs
            }}
            
            response = requests.post(
                f"{{self.base_url}}/api/chat",
                json=payload,
                timeout=120
            )
            response.raise_for_status()
            
            result = response.json()
            
            return {{
                "message": result.get("message", {{}}).get("content", ""),
                "model": model,
                "platform": "{name}",
                "local": True
            }}
            
        except requests.exceptions.RequestException as e:
            return {{
                "error": str(e),
                "model": model,
                "platform": "{name}"
            }}


if __name__ == "__main__":
    platform = {name.replace(" ", "").replace("-", "")}Platform()
    
    print(f"{name} Platform")
    print(f"Installed: {{platform.is_installed()}}")
    print(f"Models directory: {{platform.models_dir}}")
    
    if platform.is_installed():
        print(f"\\nAvailable models:")
        for model in platform.list_models():
            print(f"  - {{model}}")
'''
        
        (platform_dir / "platform.py").write_text(platform_content, encoding='utf-8')
        
        # Config
        config = {
            "name": name,
            "type": "local_model_platform",
            "executable": executable,
            "default_port": default_port,
            "models_dir": models_dir,
            "requires_internet": False,
            "supports_gpu": True
        }
        
        (platform_dir / "config.json").write_text(
            json.dumps(config, indent=2), encoding='utf-8'
        )
        
        # README
        readme = f'''# {name} Platform

Local model inference platform - no cloud required.

## Installation

```bash
# The platform will auto-install if not detected
# Or install manually from official source
```

## Usage

```python
from plugins.local_models.{name.lower().replace(" ", "_")} import {name.replace(" ", "").replace("-", "")}Platform

# Initialize
platform = {name.replace(" ", "").replace("-", "")}Platform()

# Start server
platform.start_server()

# List models
models = platform.list_models()

# Pull a model
platform.pull_model("llama2:7b")

# Generate
result = platform.generate(
    prompt="Explain AI",
    model="llama2:7b"
)

# Chat
response = platform.chat(
    messages=[{{"role": "user", "content": "Hello!"}}],
    model="llama2:7b"
)

# Cleanup
platform.stop_server()
```

## Features

- ✅ Fully local - no internet required after model download
- ✅ Privacy-focused - data never leaves your machine
- ✅ GPU acceleration supported
- ✅ Multiple model formats
- ✅ Easy model management

## Configuration

- **Port:** {default_port}
- **Models Directory:** {models_dir}
- **Executable:** {executable}
'''
        
        (platform_dir / "README.md").write_text(readme, encoding='utf-8')
        
        print(f"✅ Created {name} platform at: {platform_dir}")


def main():
    """Generate all local model platform plugins"""
    repo_root = Path.cwd()
    generator = LocalModelGenerator(repo_root)
    
    print("=" * 80)
    print("GENERATING LOCAL MODEL PLATFORM PLUGINS")
    print("=" * 80)
    print()
    
    platforms = [
        {"name": "Ollama", "executable": "ollama", "port": 11434, "models_dir": "~/.ollama/models"},
        {"name": "LM Studio", "executable": "lms", "port": 1234, "models_dir": "~/.cache/lm-studio"},
        {"name": "GPT4All", "executable": "gpt4all", "port": 4891, "models_dir": "~/.local/share/nomic.ai/GPT4All"},
        {"name": "LocalAI", "executable": "local-ai", "port": 8080, "models_dir": "~/.local/share/local-ai"},
        {"name": "Jan", "executable": "jan", "port": 1337, "models_dir": "~/jan/models"},
        {"name": "KoboldAI", "executable": "koboldcpp", "port": 5001, "models_dir": "~/KoboldAI/models"},
        {"name": "Text Generation WebUI", "executable": "python", "port": 7860, "models_dir": "~/text-generation-webui/models"},
        {"name": "llama.cpp", "executable": "llama-server", "port": 8080, "models_dir": "~/llama.cpp/models"},
        {"name": "vLLM", "executable": "vllm", "port": 8000, "models_dir": "~/.cache/huggingface"},
        {"name": "ExLlama", "executable": "exllama", "port": 5000, "models_dir": "~/exllama/models"},
    ]
    
    for platform in platforms:
        generator.generate_local_platform(
            platform["name"],
            platform["executable"],
            platform["port"],
            platform["models_dir"]
        )
    
    print()
    print("=" * 80)
    print(f"COMPLETE: Created {len(platforms)} local model platforms")
    print("=" * 80)


if __name__ == "__main__":
    main()
