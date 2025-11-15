"""
GPT4All-J Local Model Platform
"""

import subprocess
from pathlib import Path


class GPT4AllJPlatform:
    def __init__(self, port=4891):
        self.name = "GPT4All-J"
        self.port = port
        self.executable = "gpt4all-j"
        self.models_dir = Path("~/.local/share/nomic.ai").expanduser()
    
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
