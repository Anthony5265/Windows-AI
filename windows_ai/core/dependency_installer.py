"""
Dependency Installer - Auto-installs all required packages
Handles package installation, version management, and fallbacks
"""

import asyncio
import logging
import subprocess
import sys
from typing import Dict, List, Optional, Tuple
import importlib.util

logger = logging.getLogger(__name__)

class DependencyInstaller:
    """Automatic dependency installation and management"""

    def __init__(self):
        self.required_packages = self._get_required_packages()
        self.optional_packages = self._get_optional_packages()
        self.installed = []
        self.failed = []

    def _get_required_packages(self) -> Dict[str, str]:
        """Core packages required for basic functionality"""
        return {
            # Core AI/ML
            "openai": "openai>=1.0.0",
            "anthropic": "anthropic>=0.18.0",
            "google-generativeai": "google-generativeai>=0.3.0",
            "langchain": "langchain>=0.1.0",
            "langchain-community": "langchain-community>=0.0.20",
            "llama-index": "llama-index>=0.9.0",

            # HTTP/API
            "aiohttp": "aiohttp>=3.9.0",
            "requests": "requests>=2.31.0",
            "httpx": "httpx>=0.25.0",

            # Data processing
            "numpy": "numpy>=1.24.0",
            "pandas": "pandas>=2.0.0",
            "pillow": "pillow>=10.0.0",

            # Utilities
            "python-dotenv": "python-dotenv>=1.0.0",
            "pydantic": "pydantic>=2.0.0",
            "tqdm": "tqdm>=4.65.0",
            "psutil": "psutil>=5.9.0"
        }

    def _get_optional_packages(self) -> Dict[str, Dict]:
        """Optional packages organized by feature"""
        return {
            # AI Providers
            "mistralai": {"package": "mistralai>=0.0.11", "feature": "Mistral AI"},
            "cohere": {"package": "cohere>=4.0.0", "feature": "Cohere AI"},
            "groq": {"package": "groq>=0.4.0", "feature": "Groq AI"},

            # Computer Vision
            "opencv-python": {"package": "opencv-python>=4.8.0", "feature": "Computer Vision"},
            "ultralytics": {"package": "ultralytics>=8.0.0", "feature": "YOLO Object Detection"},
            "deepface": {"package": "deepface>=0.0.79", "feature": "Face Recognition"},
            "mediapipe": {"package": "mediapipe>=0.10.0", "feature": "MediaPipe"},

            # Audio/Speech
            "openai-whisper": {"package": "openai-whisper>=20231117", "feature": "Whisper STT"},
            "elevenlabs": {"package": "elevenlabs>=0.2.0", "feature": "ElevenLabs TTS"},
            "pydub": {"package": "pydub>=0.25.0", "feature": "Audio Processing"},
            "librosa": {"package": "librosa>=0.10.0", "feature": "Audio Analysis"},

            # NLP/Embeddings
            "sentence-transformers": {"package": "sentence-transformers>=2.2.0", "feature": "Embeddings"},
            "transformers": {"package": "transformers>=4.35.0", "feature": "Hugging Face Models"},
            "spacy": {"package": "spacy>=3.7.0", "feature": "SpaCy NLP"},
            "nltk": {"package": "nltk>=3.8.0", "feature": "NLTK"},

            # Vector Databases
            "chromadb": {"package": "chromadb>=0.4.0", "feature": "ChromaDB"},
            "pinecone-client": {"package": "pinecone-client>=3.0.0", "feature": "Pinecone"},
            "qdrant-client": {"package": "qdrant-client>=1.7.0", "feature": "Qdrant"},
            "weaviate-client": {"package": "weaviate-client>=3.26.0", "feature": "Weaviate"},
            "pymilvus": {"package": "pymilvus>=2.3.0", "feature": "Milvus"},
            "faiss-cpu": {"package": "faiss-cpu>=1.7.0", "feature": "FAISS"},

            # Databases
            "psycopg2-binary": {"package": "psycopg2-binary>=2.9.0", "feature": "PostgreSQL"},
            "pymongo": {"package": "pymongo>=4.6.0", "feature": "MongoDB"},
            "redis": {"package": "redis>=5.0.0", "feature": "Redis"},
            "motor": {"package": "motor>=3.3.0", "feature": "MongoDB Async"},
            "asyncpg": {"package": "asyncpg>=0.29.0", "feature": "PostgreSQL Async"},
            "aiomysql": {"package": "aiomysql>=0.2.0", "feature": "MySQL Async"},

            # Cloud/Storage
            "boto3": {"package": "boto3>=1.34.0", "feature": "AWS S3"},
            "google-cloud-storage": {"package": "google-cloud-storage>=2.10.0", "feature": "GCS"},
            "azure-storage-blob": {"package": "azure-storage-blob>=12.19.0", "feature": "Azure Blob"},

            # Workflow/Automation
            "selenium": {"package": "selenium>=4.15.0", "feature": "Browser Automation"},
            "playwright": {"package": "playwright>=1.40.0", "feature": "Playwright"},
            "pyautogui": {"package": "pyautogui>=0.9.54", "feature": "GUI Automation"},
            "pywinauto": {"package": "pywinauto>=0.6.8", "feature": "Windows Automation"},

            # Document Processing
            "pypdf": {"package": "pypdf>=3.17.0", "feature": "PDF Processing"},
            "python-docx": {"package": "python-docx>=1.1.0", "feature": "Word Documents"},
            "openpyxl": {"package": "openpyxl>=3.1.0", "feature": "Excel Files"},
            "pytesseract": {"package": "pytesseract>=0.3.10", "feature": "OCR"},
            "pdf2image": {"package": "pdf2image>=1.16.0", "feature": "PDF to Image"},

            # Email/Notifications
            "sendgrid": {"package": "sendgrid>=6.11.0", "feature": "SendGrid Email"},
            "twilio": {"package": "twilio>=8.11.0", "feature": "Twilio SMS"},
            "slack-sdk": {"package": "slack-sdk>=3.26.0", "feature": "Slack"},
            "discord.py": {"package": "discord.py>=2.3.0", "feature": "Discord"},

            # Monitoring/Analytics
            "sentry-sdk": {"package": "sentry-sdk>=1.39.0", "feature": "Sentry"},
            "prometheus-client": {"package": "prometheus-client>=0.19.0", "feature": "Prometheus"},

            # AI Frameworks
            "crewai": {"package": "crewai>=0.1.0", "feature": "CrewAI"},
            "autogen-agentchat": {"package": "pyautogen>=0.2.0", "feature": "AutoGen"},
            "semantic-kernel": {"package": "semantic-kernel>=0.4.0", "feature": "Semantic Kernel"},

            # MCP Servers
            "mcp": {"package": "mcp>=0.1.0", "feature": "Model Context Protocol"},

            # ML/DL
            "torch": {"package": "torch>=2.1.0", "feature": "PyTorch"},
            "tensorflow": {"package": "tensorflow>=2.15.0", "feature": "TensorFlow"},
            "scikit-learn": {"package": "scikit-learn>=1.3.0", "feature": "Scikit-learn"},
            "xgboost": {"package": "xgboost>=2.0.0", "feature": "XGBoost"},

            # API/Web
            "fastapi": {"package": "fastapi>=0.108.0", "feature": "FastAPI"},
            "uvicorn": {"package": "uvicorn>=0.25.0", "feature": "Uvicorn"},
            "flask": {"package": "flask>=3.0.0", "feature": "Flask"},
            "streamlit": {"package": "streamlit>=1.29.0", "feature": "Streamlit"},

            # Utilities
            "pyotp": {"package": "pyotp>=2.9.0", "feature": "2FA/TOTP"},
            "qrcode": {"package": "qrcode>=7.4.0", "feature": "QR Codes"},
            "beautifulsoup4": {"package": "beautifulsoup4>=4.12.0", "feature": "HTML Parsing"},
            "lxml": {"package": "lxml>=5.0.0", "feature": "XML Processing"},
            "jsonschema": {"package": "jsonschema>=4.20.0", "feature": "JSON Schema"},
            "pyyaml": {"package": "pyyaml>=6.0.0", "feature": "YAML"},
            "toml": {"package": "toml>=0.10.0", "feature": "TOML"},

            # Robotics/Hardware
            "dronekit": {"package": "dronekit>=2.9.0", "feature": "Drone Control"},
            "pymodbus": {"package": "pymodbus>=3.5.0", "feature": "Modbus PLC"},
        }

    async def install_all(self):
        """Install all required dependencies.
        
        Only installs the core required packages (not optional ones).
        Optional packages are installed on-demand when features are first used.
        """
        logger.info("[*] Starting dependency installation...")

        # Only install required packages - optional ones install on demand
        logger.info(f"Installing {len(self.required_packages)} required packages...")
        for name, spec in self.required_packages.items():
            await self._install_package(name, spec, required=True)

        # Summary
        logger.info(f"[+] Installed: {len(self.installed)} packages")
        if self.failed:
            logger.warning(f"[!] Failed: {len(self.failed)} packages")
            logger.warning(f"  Failed packages: {', '.join(self.failed)}")
        
        logger.info("[*] Optional packages will be installed when features are first used.")

    async def _install_package(self, name: str, spec: str, required: bool = False, feature: str = None):
        """Install a single package"""
        # Check if already installed
        if self._is_installed(name):
            logger.debug(f"  [+] {name} already installed")
            self.installed.append(name)
            return

        try:
            logger.info(f"  [*] Installing {name}..." + (f" ({feature})" if feature else ""))

            # Use pip to install
            process = await asyncio.create_subprocess_exec(
                sys.executable, "-m", "pip", "install", spec, "-q",
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )

            stdout, stderr = await process.communicate()

            if process.returncode == 0:
                logger.info(f"  [+] Installed {name}")
                self.installed.append(name)
            else:
                raise Exception(stderr.decode())

        except Exception as e:
            if required:
                logger.error(f"  [!] Failed to install required package {name}: {e}")
            else:
                logger.warning(f"  [!] Failed to install optional package {name}: {e}")
            self.failed.append(name)

    def _is_installed(self, package_name: str) -> bool:
        """Check if a package is installed"""
        # Handle package name variations
        import_names = {
            "opencv-python": "cv2",
            "python-dotenv": "dotenv",
            "pillow": "PIL",
            "scikit-learn": "sklearn",
            "pyyaml": "yaml",
            "beautifulsoup4": "bs4",
            "python-docx": "docx",
            "google-generativeai": "google.generativeai",
            "google-cloud-storage": "google.cloud.storage",
            "azure-storage-blob": "azure.storage.blob",
            "pinecone-client": "pinecone",
            "qdrant-client": "qdrant_client",
            "weaviate-client": "weaviate",
            "openai-whisper": "whisper",
            "discord.py": "discord",
            "slack-sdk": "slack_sdk",
            "sentry-sdk": "sentry_sdk",
            "prometheus-client": "prometheus_client",
            "semantic-kernel": "semantic_kernel",
            "autogen-agentchat": "autogen",
            "psycopg2-binary": "psycopg2"
        }

        check_name = import_names.get(package_name, package_name.replace("-", "_"))

        try:
            spec = importlib.util.find_spec(check_name)
            return spec is not None
        except (ImportError, ModuleNotFoundError, ValueError):
            return False

    def get_install_status(self) -> Dict:
        """Get installation status report"""
        total = len(self.required_packages) + len(self.optional_packages)
        return {
            "total_packages": total,
            "installed": len(self.installed),
            "failed": len(self.failed),
            "success_rate": len(self.installed) / total if total > 0 else 0,
            "failed_packages": self.failed
        }
