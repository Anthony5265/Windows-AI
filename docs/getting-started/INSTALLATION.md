# Windows AI Installation Guide

Complete step-by-step installation instructions for Windows AI.

---

## Table of Contents

1. [Prerequisites](#prerequisites)
2. [Installation Methods](#installation-methods)
3. [Method 1: Binary Installer (Recommended)](#method-1-binary-installer-recommended)
4. [Method 2: Python Package](#method-2-python-package)
5. [Method 3: From Source](#method-3-from-source)
6. [Post-Installation Setup](#post-installation-setup)
7. [Verification](#verification)
8. [Optional Components](#optional-components)
9. [Troubleshooting](#troubleshooting)
10. [Uninstallation](#uninstallation)

---

## Prerequisites

### System Requirements

**Minimum:**
- Windows 10 (64-bit) version 1809 or later
- 8 GB RAM
- 10 GB free disk space
- Intel Core i5 or equivalent CPU
- Internet connection (for initial setup and cloud models)

**Recommended:**
- Windows 11 (64-bit)
- 16 GB RAM
- 50 GB free disk space (for local AI models)
- Intel Core i7 or AMD Ryzen 7
- NVIDIA GPU with 8GB+ VRAM (for local image generation)
- SSD storage
- Stable internet connection

### Software Prerequisites

The installer handles most dependencies automatically, but you may want to install these first:

- **Python 3.8-3.12** (if installing from source)
- **Git** (optional, for source installation)
- **Visual Studio Build Tools** (optional, for some plugins)

---

## Installation Methods

Choose one of the following installation methods:

| Method | Difficulty | Use Case |
|--------|-----------|----------|
| **Binary Installer** | Easy | Most users, quick setup |
| **Python Package** | Medium | Python developers, virtual environments |
| **From Source** | Advanced | Developers, contributors, customization |

---

## Method 1: Binary Installer (Recommended)

The easiest way to install Windows AI.

### Step 1: Download the Installer

1. Go to [Releases](https://github.com/Anthony5265/Windows-AI/releases/latest)
2. Download `WindowsAI-Setup.exe` (approximately 150-200 MB)
3. Optionally verify the checksum:
   ```powershell
   Get-FileHash WindowsAI-Setup.exe -Algorithm SHA256
   ```

### Step 2: Run the Installer

1. **Right-click** `WindowsAI-Setup.exe`
2. Select **"Run as administrator"**
3. Click **"Yes"** on the User Account Control prompt

### Step 3: Installation Wizard

The installer will guide you through:

**Welcome Screen:**
- Click **"Next"**

**License Agreement:**
- Read and accept the MIT License
- Click **"I Agree"**

**Installation Location:**
- Default: `C:\Program Files\Windows AI`
- Or click **"Browse"** to choose custom location
- Click **"Next"**

**Component Selection:**
- **Core Components** (Required): ✓
- **Desktop GUI**: ✓ (Recommended)
- **CLI Tools**: ✓ (Recommended)
- **API Server**: ✓ (Recommended)
- **Examples & Docs**: ✓ (Optional)
- **Development Tools**: (Optional, for plugin development)

**Installation:**
- Click **"Install"**
- Wait for installation (5-10 minutes)
- Progress shows:
  - Extracting files
  - Installing Python dependencies
  - Configuring system integration
  - Creating shortcuts

**Completion:**
- Click **"Finish"**
- Optional: Check **"Launch Windows AI"**

### Step 4: First Launch

After installation:

1. Windows AI will launch automatically (if selected)
2. Or start from:
   - Start Menu: **Windows AI**
   - Desktop shortcut
   - Command line: `windows-ai`

---

## Method 2: Python Package

Install Windows AI as a Python package using pip.

### Prerequisites

- Python 3.8 - 3.12 installed
- pip package manager
- Virtual environment (recommended)

### Step 1: Create Virtual Environment (Recommended)

```bash
# Create virtual environment
python -m venv windows-ai-env

# Activate it
# On Windows Command Prompt:
windows-ai-env\Scripts\activate

# On PowerShell:
windows-ai-env\Scripts\Activate.ps1
```

### Step 2: Install Windows AI

```bash
# Install from PyPI (when published)
pip install windows-ai

# Or install with optional dependencies
pip install windows-ai[all]

# Install specific feature sets
pip install windows-ai[api,gui,dev]
```

### Step 3: Verify Installation

```bash
windows-ai --version
windows-ai --help
```

---

## Method 3: From Source

For developers who want to customize or contribute.

### Step 1: Install Prerequisites

1. **Python 3.8-3.12**
   ```bash
   python --version  # Should be 3.8 or higher
   ```

2. **Git**
   ```bash
   git --version
   ```

3. **Visual Studio Build Tools** (optional, for C extensions)
   - Download from [Visual Studio Downloads](https://visualstudio.microsoft.com/downloads/)
   - Select "Desktop development with C++"

### Step 2: Clone Repository

```bash
# Clone the repository
git clone https://github.com/Anthony5265/Windows-AI.git
cd Windows-AI

# Or clone your fork
git clone https://github.com/YOUR_USERNAME/Windows-AI.git
cd Windows-AI
```

### Step 3: Create Virtual Environment

```bash
# Create virtual environment
python -m venv venv

# Activate it
# Windows Command Prompt:
venv\Scripts\activate

# PowerShell:
venv\Scripts\Activate.ps1

# Git Bash:
source venv/Scripts/activate
```

### Step 4: Install in Development Mode

```bash
# Upgrade pip
python -m pip install --upgrade pip

# Install development dependencies
pip install -e .[dev]

# Or install all optional dependencies
pip install -e .[all]
```

This installs Windows AI in "editable" mode - changes to the code take effect immediately.

### Step 5: Verify Installation

```bash
# Check installation
python -c "import windows_ai; print(windows_ai.__version__)"

# Run tests
pytest tests/

# Run the application
python -m windows_ai
```

---

## Post-Installation Setup

### Initial Configuration

When you first run Windows AI, it will:

1. **Create configuration directory:**
   - Location: `%APPDATA%\WindowsAI`
   - Contains: settings, plugins, cache, logs

2. **Run setup wizard:**
   - Choose AI provider (local, cloud, or both)
   - Configure API keys (optional)
   - Select default model
   - Choose theme (light/dark)

### Configure AI Providers

#### Local AI (Ollama)

1. Install Ollama:
   ```bash
   # Download from https://ollama.ai
   # Or Windows AI can install it for you
   windows-ai setup ollama
   ```

2. Download a model:
   ```bash
   ollama pull llama2
   # Or
   windows-ai model download llama2
   ```

#### Cloud AI (Optional)

Configure API keys for cloud providers:

**OpenAI:**
```bash
# Set via environment variable
set OPENAI_API_KEY=sk-your-key-here

# Or via Windows AI
windows-ai config set providers.openai.api_key YOUR_KEY
```

**Anthropic:**
```bash
set ANTHROPIC_API_KEY=sk-ant-your-key-here
# Or
windows-ai config set providers.anthropic.api_key YOUR_KEY
```

**Google:**
```bash
set GOOGLE_API_KEY=your-key-here
# Or
windows-ai config set providers.google.api_key YOUR_KEY
```

### System Integration

#### Add to PATH (if needed)

The installer usually adds Windows AI to PATH automatically. If not:

1. **Open System Properties:**
   - Press `Win + Pause`
   - Click "Advanced system settings"
   - Click "Environment Variables"

2. **Edit PATH:**
   - Under "System variables", select "Path"
   - Click "Edit"
   - Click "New"
   - Add: `C:\Program Files\Windows AI\bin`
   - Click "OK"

3. **Verify:**
   ```bash
   # Close and reopen command prompt
   windows-ai --version
   ```

#### Windows Defender Exclusion (Optional)

For better performance, exclude Windows AI from real-time scanning:

1. **Open Windows Security**
2. **Virus & threat protection** → **Manage settings**
3. **Exclusions** → **Add or remove exclusions**
4. **Add an exclusion** → **Folder**
5. Select: `C:\Program Files\Windows AI`

---

## Verification

### Test Core Functionality

```bash
# Test CLI
windows-ai version
windows-ai status

# Test Python API
python -c "
import asyncio
from windows_ai import quick_start

async def test():
    ai = await quick_start()
    print('Windows AI initialized successfully!')

asyncio.run(test())
"

# Test REST API
windows-ai serve &
curl http://localhost:8765/api/health
```

### Run System Tests

```bash
# Basic smoke test
windows-ai test

# Comprehensive test suite (if installed from source)
pytest tests/ -v

# Test specific components
windows-ai test --component plugins
windows-ai test --component api
windows-ai test --component agents
```

---

## Optional Components

### Desktop GUI

The GUI is under development. To install the current version:

```bash
# Install GUI dependencies
pip install windows-ai[gui]

# Launch GUI
windows-ai gui
```

### System Tray Integration

```bash
# Install tray dependencies
pip install windows-ai[tray]

# Enable tray
windows-ai config set system.tray.enabled true

# Start tray app
windows-ai tray
```

### Additional Models

Download popular AI models:

```bash
# List available models
windows-ai model list-available

# Download specific models
windows-ai model download llama2:7b
windows-ai model download llama2:13b
windows-ai model download mistral:7b
windows-ai model download codellama:7b

# Check downloaded models
windows-ai model list
```

### Plugin Packs

Install additional plugins:

```bash
# List available plugin packs
windows-ai plugin packs

# Install specific packs
windows-ai plugin install-pack development
windows-ai plugin install-pack productivity
windows-ai plugin install-pack media

# Or install individual plugins
windows-ai plugin install github-enhanced
windows-ai plugin install file-organizer
```

---

## Troubleshooting

### Installation Fails

**Problem:** Installer crashes or hangs

**Solutions:**
1. Run as Administrator
2. Temporarily disable antivirus
3. Check disk space (need 10GB+)
4. Download installer again (may be corrupted)
5. Check Windows Event Viewer for errors

**Problem:** "Python not found" error

**Solutions:**
1. Install Python 3.8-3.12 from python.org
2. During Python installation, check "Add Python to PATH"
3. Restart computer after Python installation

### Dependency Errors

**Problem:** pip install fails with "Microsoft Visual C++ 14.0 is required"

**Solutions:**
1. Install Visual Studio Build Tools
2. Or install pre-built wheels:
   ```bash
   pip install --only-binary :all: windows-ai
   ```

**Problem:** Specific package fails to install

**Solutions:**
```bash
# Skip problematic optional dependencies
pip install windows-ai --no-deps
pip install -r requirements.txt --skip-errors

# Or install core only
pip install windows-ai[core]
```

### Configuration Issues

**Problem:** "Cannot find configuration file"

**Solutions:**
```bash
# Reset configuration
windows-ai config reset

# Manually create config directory
mkdir %APPDATA%\WindowsAI
windows-ai config init
```

**Problem:** Permission denied errors

**Solutions:**
1. Run as Administrator
2. Or change installation directory to user folder
3. Check folder permissions

### Model Download Issues

**Problem:** Model download fails or is slow

**Solutions:**
```bash
# Use different mirror
windows-ai model download llama2 --mirror https://mirror.example.com

# Resume interrupted download
windows-ai model download llama2 --resume

# Download to custom location
windows-ai model download llama2 --path D:\AI-Models
```

### API Connection Issues

**Problem:** "Cannot connect to API server"

**Solutions:**
```bash
# Check if server is running
windows-ai status

# Start server manually
windows-ai serve --port 8765

# Check firewall settings
# Allow inbound connections on port 8765
```

### Getting Help

If you encounter issues not covered here:

1. **Check Logs:**
   ```bash
   # View recent logs
   windows-ai logs

   # Or manually check
   notepad %APPDATA%\WindowsAI\logs\windows-ai.log
   ```

2. **Run Diagnostics:**
   ```bash
   windows-ai diagnose
   # Generates diagnostic report
   ```

3. **Community Support:**
   - GitHub Issues: Report bugs
   - GitHub Discussions: Ask questions
   - Documentation: Check guides

---

## Uninstallation

### Method 1: Using Windows Settings

1. **Open Settings** (Win + I)
2. **Apps** → **Apps & features**
3. Find **"Windows AI"**
4. Click **Uninstall**
5. Follow prompts

### Method 2: Using Control Panel

1. **Control Panel** → **Programs** → **Programs and Features**
2. Find **"Windows AI"**
3. Right-click → **Uninstall**
4. Follow prompts

### Method 3: Using pip

If installed via pip:

```bash
pip uninstall windows-ai

# Remove all dependencies
pip uninstall -r requirements.txt -y
```

### Clean Uninstall

To remove all data and settings:

```bash
# Before uninstalling, backup if needed
windows-ai backup create

# Then remove everything
rmdir /s "%APPDATA%\WindowsAI"
rmdir /s "%LOCALAPPDATA%\WindowsAI"
rmdir /s "%PROGRAMFILES%\Windows AI"

# Remove from PATH (if needed)
# Follow PATH removal steps in System Properties
```

---

## Next Steps

After installation:

1. **Read the [Quick Start Guide](../QUICK_START.md)** - Get started in 5 minutes
2. **Explore [Examples](../examples/README.md)** - See what Windows AI can do
3. **Check the [User Guide](../USER_GUIDE.md)** - Learn all features
4. **Browse the [API docs](../api/README.md)** - Explore API and provider routes

---

## Frequently Asked Questions

**Q: How much disk space do I need?**

A: Minimum 10GB, but 50GB+ recommended if using local models.

**Q: Do I need an NVIDIA GPU?**

A: No, CPU works fine. GPU is optional for faster local image generation.

**Q: Can I use Windows AI offline?**

A: Yes! With local models (Ollama), Windows AI works 100% offline.

**Q: How do I update Windows AI?**

A:
```bash
# Via installer: Download latest version
# Via pip:
pip install --upgrade windows-ai
# Built-in updater:
windows-ai update
```

**Q: Is my data secure?**

A: Yes. By default, everything runs locally. Cloud providers are optional and only used when you explicitly request them.

---

**Installation complete!** Ready to get started? Continue to the [Quick Start Guide](../QUICK_START.md).
