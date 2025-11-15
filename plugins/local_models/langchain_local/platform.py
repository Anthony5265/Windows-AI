"""
LangChain Local Local Model Platform
"""

import subprocess
from pathlib import Path


class LangChainLocalPlatform:
    def __init__(self, port=5000):
        self.name = "LangChain Local"
        self.port = port
        self.executable = "python"
        self.models_dir = Path("~/langchain-local").expanduser()
    
    def is_installed(self):
        try:
            subprocess.run([self.executable, "--version"], capture_output=True, timeout=5)
            return True
        except:
            return False
    
    def start_server(self):
        print(f"Starting {self.name} on port {self.port}")
        # Start server implementation
    
    def list_models(self):
        if self.models_dir.exists():
            return [f.name for f in self.models_dir.iterdir() if f.is_file()]
        return []
