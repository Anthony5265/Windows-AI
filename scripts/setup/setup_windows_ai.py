#!/usr/bin/env python3
"""
Windows AI - One-Click Setup Orchestrator
Automatically sets up the entire Windows AI environment
"""

import os
import sys
import subprocess
import platform
import shutil
import urllib.request
import zipfile
import json
from pathlib import Path
from typing import Optional, List, Dict

class WindowsAISetup:
    """Orchestrates the complete Windows AI setup"""

    def __init__(self):
        self.home_dir = Path.home()
        self.install_dir = self.home_dir / ".windowsai"
        self.data_dir = self.install_dir / "data"
        self.models_dir = self.install_dir / "models"
        self.config_dir = self.install_dir / "config"
        self.logs_dir = self.install_dir / "logs"
        self.is_windows = platform.system() == "Windows"
        self.python_cmd = sys.executable

    def run(self, options: Optional[Dict] = None):
        """Run the complete setup"""
        options = options or {}

        print("=" * 60)
        print("     WINDOWS AI - ONE-CLICK SETUP")
        print("=" * 60)
        print()

        steps = [
            ("Creating directories", self.create_directories),
            ("Checking Python version", self.check_python),
            ("Installing Python dependencies", self.install_python_deps),
            ("Creating default configuration", self.create_config),
            ("Setting up environment variables", self.setup_environment),
        ]

        # Optional steps based on user preferences
        if options.get("install_ollama", True):
            steps.append(("Setting up Ollama (local AI)", self.setup_ollama))

        if options.get("install_nodejs", False):
            steps.append(("Installing Node.js dependencies", self.install_nodejs))

        if options.get("download_models", False):
            steps.append(("Downloading default models", self.download_models))

        steps.append(("Finalizing setup", self.finalize))

        total = len(steps)
        for i, (name, func) in enumerate(steps, 1):
            print(f"\n[{i}/{total}] {name}...")
            try:
                func()
                print(f"    Done!")
            except Exception as e:
                print(f"    Warning: {e}")
                if options.get("strict", False):
                    raise

        print("\n" + "=" * 60)
        print("     SETUP COMPLETE!")
        print("=" * 60)
        print(f"\nInstallation directory: {self.install_dir}")
        print("\nTo start Windows AI:")
        print("  python -m windows_ai --api")
        print("\nOr if installed as package:")
        print("  windows-ai --api")
        print()

    def create_directories(self):
        """Create necessary directories"""
        dirs = [
            self.install_dir,
            self.data_dir,
            self.models_dir,
            self.config_dir,
            self.logs_dir,
            self.install_dir / "plugins",
            self.install_dir / "cache",
        ]
        for d in dirs:
            d.mkdir(parents=True, exist_ok=True)

    def check_python(self):
        """Check Python version"""
        version = sys.version_info
        if version < (3, 8):
            raise RuntimeError(f"Python 3.8+ required, found {version.major}.{version.minor}")
        print(f"    Python {version.major}.{version.minor}.{version.micro}")

    def install_python_deps(self):
        """Install Python dependencies"""
        # Find requirements file
        req_files = [
            Path(__file__).parent / "requirements-full.txt",
            Path(__file__).parent / "requirements.txt",
        ]

        req_file = None
        for rf in req_files:
            if rf.exists():
                req_file = rf
                break

        if req_file:
            subprocess.run(
                [self.python_cmd, "-m", "pip", "install", "-r", str(req_file), "-q"],
                check=False
            )
        else:
            # Install core dependencies directly
            core_deps = [
                "fastapi", "uvicorn", "httpx", "pydantic",
                "openai", "anthropic", "litellm",
                "langchain", "langchain-community",
                "chromadb", "pyyaml", "psutil"
            ]
            subprocess.run(
                [self.python_cmd, "-m", "pip", "install"] + core_deps + ["-q"],
                check=False
            )

    def create_config(self):
        """Create default configuration"""
        config = {
            "version": "2.0.0",
            "api": {
                "host": "127.0.0.1",
                "port": 8765,
                "cors_origins": ["*"]
            },
            "security": {
                "sandbox_level": "standard",
                "guardrails": True,
                "require_auth": False
            },
            "llm": {
                "default_provider": "openai",
                "fallback_providers": ["ollama", "anthropic"]
            },
            "storage": {
                "data_dir": str(self.data_dir),
                "models_dir": str(self.models_dir)
            },
            "features": {
                "mcp_enabled": True,
                "local_llm": True,
                "cloud_sync": False
            }
        }

        config_file = self.config_dir / "config.yaml"
        if not config_file.exists():
            import yaml
            with open(config_file, 'w') as f:
                yaml.dump(config, f, default_flow_style=False)

        # Create .env template
        env_template = self.config_dir / ".env.template"
        env_content = """# Windows AI Environment Variables
# Copy this to .env and fill in your API keys

# OpenAI
OPENAI_API_KEY=

# Anthropic
ANTHROPIC_API_KEY=

# Google AI
GOOGLE_API_KEY=

# Mistral
MISTRAL_API_KEY=

# Groq (fast inference)
GROQ_API_KEY=

# Cohere
COHERE_API_KEY=

# Together AI
TOGETHER_API_KEY=

# Local LLM (Ollama)
OLLAMA_HOST=http://localhost:11434
"""
        env_template.write_text(env_content)

    def setup_environment(self):
        """Set up environment variables"""
        # Create activation script
        if self.is_windows:
            script = self.install_dir / "activate.bat"
            content = f"""@echo off
set WINDOWSAI_HOME={self.install_dir}
set WINDOWSAI_CONFIG={self.config_dir}
set PATH=%PATH%;{self.install_dir}
echo Windows AI environment activated
"""
        else:
            script = self.install_dir / "activate.sh"
            content = f"""#!/bin/bash
export WINDOWSAI_HOME="{self.install_dir}"
export WINDOWSAI_CONFIG="{self.config_dir}"
export PATH="$PATH:{self.install_dir}"
echo "Windows AI environment activated"
"""
        script.write_text(content)

    def setup_ollama(self):
        """Set up Ollama for local LLM support"""
        # Check if Ollama is installed
        ollama_cmd = "ollama" if not self.is_windows else "ollama.exe"

        if shutil.which(ollama_cmd):
            print("    Ollama already installed")
            # Try to pull a lightweight model
            try:
                subprocess.run(
                    [ollama_cmd, "pull", "llama3.2:1b"],
                    capture_output=True,
                    timeout=300
                )
            except Exception:
                pass
        else:
            print("    Ollama not found - visit https://ollama.ai to install")

    def install_nodejs(self):
        """Install Node.js dependencies for MCP servers"""
        if shutil.which("npm"):
            mcp_servers = [
                "@modelcontextprotocol/server-filesystem",
                "@modelcontextprotocol/server-fetch",
                "@modelcontextprotocol/server-memory",
            ]
            for server in mcp_servers:
                try:
                    subprocess.run(
                        ["npm", "install", "-g", server],
                        capture_output=True,
                        timeout=120
                    )
                except Exception:
                    pass
        else:
            print("    npm not found - skipping MCP server installation")

    def download_models(self):
        """Download default embedding models"""
        try:
            from sentence_transformers import SentenceTransformer
            model = SentenceTransformer('all-MiniLM-L6-v2')
            print("    Downloaded embedding model: all-MiniLM-L6-v2")
        except Exception:
            print("    Embedding model download skipped")

    def finalize(self):
        """Finalize setup"""
        # Create version file
        version_file = self.install_dir / "VERSION"
        version_file.write_text("2.0.0")

        # Create setup complete marker
        marker = self.install_dir / ".setup_complete"
        marker.write_text("1")


def main():
    """Main entry point"""
    import argparse

    parser = argparse.ArgumentParser(description="Windows AI One-Click Setup")
    parser.add_argument("--no-ollama", action="store_true", help="Skip Ollama setup")
    parser.add_argument("--with-nodejs", action="store_true", help="Install Node.js MCP servers")
    parser.add_argument("--download-models", action="store_true", help="Download default models")
    parser.add_argument("--strict", action="store_true", help="Fail on any error")
    args = parser.parse_args()

    options = {
        "install_ollama": not args.no_ollama,
        "install_nodejs": args.with_nodejs,
        "download_models": args.download_models,
        "strict": args.strict,
    }

    setup = WindowsAISetup()
    setup.run(options)


if __name__ == "__main__":
    main()
