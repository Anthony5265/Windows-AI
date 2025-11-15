"""
Alpaca.cpp Local Model Platform
"""

import subprocess
from pathlib import Path


class AlpacacppPlatform:
    def __init__(self, port=8080):
        self.name = "Alpaca.cpp"
        self.port = port
        self.executable = "alpaca"
        self.models_dir = Path("~/alpaca.cpp/models").expanduser()
    
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
