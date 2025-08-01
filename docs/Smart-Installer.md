# Smart Installer Overview

This document sketches a design for an automated installer that sets up an AI ecosystem on an existing Windows 11 installation. It does **not** modify or redistribute Windows itself. Instead, it configures user-space applications and tools.

## Goals
- Detect hardware capabilities (CPU, GPU, RAM, storage).
- Prompt the user for API keys or automatically download models that run locally.
- Offer a catalog of free and paid AI tools, plugins, and frameworks.
- Handle conflicts or missing dependencies by creating isolated environments.
- Provide a simple GUI so users can perform an "install everything" option or select components manually.
- Store API keys securely on the machine so add-ons can access them.

## High-Level Flow
1. **System Scan**
   - Use PowerShell or a Python script with the `wmi` package to collect specs such as GPU model, available RAM, and disk space.
   - Determine whether the machine meets optional GPU requirements for accelerated inference.

2. **User Choices**
   - Offer presets ("Minimal", "Full", "Custom") in the installer GUI.
   - Ask whether to use remote APIs or install local LLMs. When using remote services, prompt for one or more API keys.

3. **Download and Installation**
   - For remote services, install the necessary SDKs or Python packages.
   - For local models, download compatible model weights in the background. Use progress indicators and verify checksums.
   - Install open-source tools like Transformers, LangChain, and other community packages. Include optional paid services if the user wants them.

4. **Environment Setup**
   - Create separate virtual environments (for example, with `venv` or Conda) to avoid library conflicts.
   - Register shortcuts or background tasks so the AI Control Center launches at startup.

5. **Secure Storage**
   - Store API keys in the Windows Credential Manager or an encrypted file.
   - Provide a small helper API for plugins to retrieve keys when needed.

6. **Updates and Plugins**
   - Check periodically for new plugins or tools. Allow users to review and install updates within the GUI.

## Plugin Environments

Plugins and toolsets are installed into isolated Python environments managed by
``installer.env``. Each plugin can request dependencies and the installer will
create a dedicated ``venv`` under ``~/.windows_ai/venvs/<name>`` to avoid
package conflicts.

```python
from installer import env

# ensure a virtual environment for "example-plugin"
env_path = env.create_env("example-plugin")
env.install_packages(env_path, ["requests"])
```

Run the CLI with ``--install-all`` to discover plugins and install their
dependencies in the ``plugins`` environment:

```
python -m installer.cli --install-all
```

The GUI's **Install All** button performs the same operation.

## Example Pseudocode
```python
# detect system info
import wmi
import subprocess

def detect_specs():
    c = wmi.WMI()
    gpu = c.Win32_VideoController()[0].Name
    ram_gb = int(c.Win32_ComputerSystem()[0].TotalPhysicalMemory) / 1e9
    return {
        "gpu": gpu,
        "ram_gb": ram_gb,
    }

# install a Python package
subprocess.check_call([sys.executable, "-m", "pip", "install", "transformers"])
```

This pseudocode only scratches the surface but illustrates how the installer might check hardware details and install dependencies programmatically.

## Disclaimer
This guide does not provide a modified Windows 11 build. It only describes software that runs on top of a licensed Windows installation. Always comply with Microsoft licensing terms and the policies of any third-party service.
