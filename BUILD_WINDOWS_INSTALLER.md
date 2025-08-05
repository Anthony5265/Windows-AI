# Building the Windows AI Installer

This document explains how to produce a single `WindowsAI_Installer.exe` that bundles
this repository and launches the Tkinter-based installer GUI.

Quick-start guides for using the installer are available in `docs/README.en.md`
(English) and `docs/README.es.md` (Español).

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
   ./build_installer.ps1 [-CertPath path\to\cert.pfx -TimestampServer https://timestamp.server]
   ```

   The script will:
   - Ensure `pip` and `pyinstaller` are installed
   - Install Python dependencies from `requirements.txt`
   - Package `installer/gui_installer.py` into `dist/WindowsAI_Installer.exe`
   - Copy runtime assets (`install`, `plugins`, `assets`, `config`, `control_center`,
     `automation`, `windows_ai`) into the `dist/` folder alongside the executable
   - Optionally sign `dist\WindowsAI_Installer.exe` with `SignTool.exe` if `-CertPath`
     and `-TimestampServer` are provided

3. After the script completes, the executable is located at `dist/WindowsAI_Installer.exe`.

### Code Signing (optional)

To distribute a signed installer, supply a code signing certificate and a timestamp
server when running the build script. `SignTool.exe` from the Windows SDK must be
available in your `PATH`.

```powershell
./build_installer.ps1 -CertPath C:\path\to\cert.pfx -TimestampServer https://timestamp.digicert.com
```

The script will invoke `SignTool.exe` to sign the generated `WindowsAI_Installer.exe`.

## Testing the Installer

1. Transfer the `dist` folder to a Windows machine if built elsewhere.
2. Run `WindowsAI_Installer.exe`. The Tkinter GUI will appear and can perform
    system detection, environment-based key management, and dependency
    installation.
   After closing the GUI, the installer automatically runs
   `install\install.ps1` with administrator rights to register services,
   firewall rules, and other system integrations. Windows will prompt for
   elevation; approve the prompt to complete setup.
3. (Optional) Add the context menu entry by double-clicking
   `install\context_menu_add.reg`.

To remove integrations, use `install\uninstall.ps1` and
`install\context_menu_remove.reg`.

## Non-interactive CLI mode

The prototype installer exposes a Python CLI in `installer/cli.py`. When
automating setup, invoke it with the `--non-interactive` (or `--yes`) flag to
skip API key prompts and decline launching the Control Center GUI:

```bash
python -m installer.cli --non-interactive
```

## Updating

When repository changes occur, rerun the build script to generate an updated
installer. The script can be extended to include new assets or additional
PyInstaller options as features evolve.
