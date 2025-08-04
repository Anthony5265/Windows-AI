# Building the Windows AI Installer

This document explains how to produce a single `WindowsAI_Installer.exe` that bundles
this repository and launches the Tkinter-based installer GUI.

## Prerequisites

- Windows 10 or later
- [Python 3.11+](https://www.python.org/downloads/) in your `PATH`
- PowerShell 5.1 or PowerShell 7
- Internet connection to download Python packages and Node modules

Optional but recommended:
- [Node.js 18+](https://nodejs.org/) for components that use Node
- `winget` for package installation

## Steps to Build

1. Clone this repository and open a PowerShell terminal in the repo root.
2. Run the build script:

   ```powershell
   ./build_installer.ps1
   ```

   The script will:
   - Ensure `pip` and `pyinstaller` are installed
   - Install Python dependencies from `requirements.txt`
   - Package `installer/gui_installer.py` into `dist/WindowsAI_Installer.exe`
   - Copy runtime assets (`install`, `plugins`, `assets`, `config`, `control_center`,
     `automation`, `windows_ai`) into the `dist/` folder alongside the executable

3. After the script completes, the executable is located at `dist/WindowsAI_Installer.exe`.

## Testing the Installer

1. Transfer the `dist` folder to a Windows machine if built elsewhere.
2. Run `WindowsAI_Installer.exe`. The Tkinter GUI will appear and can perform
   system detection, API-key management, and dependency installation.
3. After running the installer GUI, execute additional setup steps:

   ```powershell
   powershell -ExecutionPolicy Bypass -File install\install.ps1
   ```

   This registers services, firewall rules, and other system integrations.
4. (Optional) Add the context menu entry by double-clicking
   `install\context_menu_add.reg`.

To remove integrations, use `install\uninstall.ps1` and
`install\context_menu_remove.reg`.

## Updating

When repository changes occur, rerun the build script to generate an updated
installer. The script can be extended to include new assets or additional
PyInstaller options as features evolve.
