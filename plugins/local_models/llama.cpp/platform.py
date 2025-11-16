"""
llama.cpp Platform Implementation
Local model inference platform
"""

import subprocess
import requests
import time
from pathlib import Path
from typing import List, Dict, Optional, Any
import json


class llama.cppPlatform:
    """
    llama.cpp Local Model Platform
    
    Manages local model inference without cloud dependencies
    """
    
    def __init__(self, models_dir: Optional[str] = None, port: int = 8080):
        """
        Initialize llama.cpp platform
        
        Args:
            models_dir: Directory containing models (default: ~/llama.cpp/models)
            port: Port for local server (default: 8080)
        """
        self.models_dir = Path(models_dir or "~/llama.cpp/models").expanduser()
        self.port = port
        self.base_url = f"http://localhost:{port}"
        self.process = None
        self.executable = "llama-server"
    
    def is_installed(self) -> bool:
        """Check if llama.cpp is installed"""
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
        """Install llama.cpp platform"""
        print(f"Installing llama.cpp...")
        try:
            # Platform-specific installation
            if "llama.cpp" == "ollama":
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
                print(f"Please install llama.cpp manually from official website")
                return False
        except Exception as e:
            print(f"Installation failed: {e}")
            return False
    
    def start_server(self, background: bool = True) -> bool:
        """Start local model server"""
        if not self.is_installed():
            print(f"{self.executable} not found. Installing...")
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
                    requests.get(f"{self.base_url}/api/tags", timeout=5)
                    print(f"✅ llama.cpp server started on port {self.port}")
                    return True
                except requests.exceptions.RequestException:
                    print(f"❌ Server failed to start")
                    return False
            else:
                subprocess.run([self.executable, "serve"])
                return True
                
        except Exception as e:
            print(f"Failed to start server: {e}")
            return False
    
    def stop_server(self):
        """Stop local model server"""
        if self.process:
            self.process.terminate()
            self.process.wait()
            print(f"✅ llama.cpp server stopped")
    
    def list_models(self) -> List[str]:
        """List locally available models"""
        try:
            response = requests.get(f"{self.base_url}/api/tags")
            response.raise_for_status()
            data = response.json()
            return [model["name"] for model in data.get("models", [])]
        except requests.exceptions.RequestException:
            return []
    
    def pull_model(self, model_name: str) -> bool:
        """Download a model"""
        try:
            print(f"Downloading {model_name}...")
            response = requests.post(
                f"{self.base_url}/api/pull",
                json={"name": model_name},
                stream=True
            )
            
            for line in response.iter_lines():
                if line:
                    status = json.loads(line)
                    if "status" in status:
                        print(f"  {status['status']}")
            
            print(f"✅ Downloaded {model_name}")
            return True
            
        except Exception as e:
            print(f"❌ Failed to download {model_name}: {e}")
            return False
    
    def generate(self, prompt: str, model: str, **kwargs) -> Dict[str, Any]:
        """Generate completion"""
        try:
            payload = {
                "model": model,
                "prompt": prompt,
                **kwargs
            }
            
            response = requests.post(
                f"{self.base_url}/api/generate",
                json=payload,
                timeout=120
            )
            response.raise_for_status()
            
            result = response.json()
            
            return {
                "text": result.get("response", ""),
                "model": model,
                "platform": "llama.cpp",
                "local": True
            }
            
        except requests.exceptions.RequestException as e:
            return {
                "error": str(e),
                "model": model,
                "platform": "llama.cpp"
            }
    
    def chat(self, messages: List[Dict[str, str]], model: str, **kwargs) -> Dict[str, Any]:
        """Chat completion"""
        try:
            payload = {
                "model": model,
                "messages": messages,
                **kwargs
            }
            
            response = requests.post(
                f"{self.base_url}/api/chat",
                json=payload,
                timeout=120
            )
            response.raise_for_status()
            
            result = response.json()
            
            return {
                "message": result.get("message", {}).get("content", ""),
                "model": model,
                "platform": "llama.cpp",
                "local": True
            }
            
        except requests.exceptions.RequestException as e:
            return {
                "error": str(e),
                "model": model,
                "platform": "llama.cpp"
            }


if __name__ == "__main__":
    platform = llama.cppPlatform()
    
    print(f"llama.cpp Platform")
    print(f"Installed: {platform.is_installed()}")
    print(f"Models directory: {platform.models_dir}")
    
    if platform.is_installed():
        print(f"\nAvailable models:")
        for model in platform.list_models():
            print(f"  - {model}")
