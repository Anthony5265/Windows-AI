#!/usr/bin/env python3
"""
Windows AI - EXE Builder
Creates standalone executable using PyInstaller
"""

import os
import sys
import shutil
import subprocess
from pathlib import Path

# Build configuration
APP_NAME = "WindowsAI"
VERSION = "2.0.0"
ICON_PATH = "assets/icon.ico"
MAIN_SCRIPT = "windows_ai/__main__.py"

# PyInstaller options
PYINSTALLER_OPTS = [
    "--name", APP_NAME,
    "--onedir",  # Create directory with all dependencies
    "--windowed",  # No console window (GUI app)
    "--noconfirm",  # Replace output without asking
    "--clean",  # Clean cache before building
    # Data files to include
    "--add-data", "windows_ai/plugins;windows_ai/plugins",
    "--add-data", "windows_ai/config;windows_ai/config",
    "--add-data", "assets;assets",
    # Hidden imports that PyInstaller might miss
    "--hidden-import", "uvicorn",
    "--hidden-import", "uvicorn.logging",
    "--hidden-import", "uvicorn.loops",
    "--hidden-import", "uvicorn.loops.auto",
    "--hidden-import", "uvicorn.protocols",
    "--hidden-import", "uvicorn.protocols.http",
    "--hidden-import", "uvicorn.protocols.http.auto",
    "--hidden-import", "uvicorn.protocols.websockets",
    "--hidden-import", "uvicorn.protocols.websockets.auto",
    "--hidden-import", "uvicorn.lifespan",
    "--hidden-import", "uvicorn.lifespan.on",
    "--hidden-import", "fastapi",
    "--hidden-import", "pydantic",
    "--hidden-import", "starlette",
    "--hidden-import", "httpx",
    "--hidden-import", "aiohttp",
    "--hidden-import", "asyncio",
    "--hidden-import", "websockets",
    "--hidden-import", "openai",
    "--hidden-import", "anthropic",
    "--hidden-import", "litellm",
    "--hidden-import", "langchain",
    "--hidden-import", "llama_index",
    "--hidden-import", "chromadb",
    "--hidden-import", "faiss",
    "--hidden-import", "PIL",
    "--hidden-import", "yaml",
    "--hidden-import", "psutil",
    # Collect all submodules
    "--collect-all", "windows_ai",
    "--collect-all", "litellm",
    "--collect-all", "langchain",
    "--collect-all", "langchain_community",
]

def ensure_icon():
    """Ensure icon file exists"""
    icon_path = Path(ICON_PATH)
    if not icon_path.exists():
        icon_path.parent.mkdir(parents=True, exist_ok=True)
        # Create a simple placeholder icon message
        print(f"Note: Icon file not found at {ICON_PATH}")
        print("Building without custom icon...")
        return None
    return str(icon_path)

def clean_build():
    """Clean previous build artifacts"""
    dirs_to_clean = ["build", "dist", "__pycache__"]
    for dir_name in dirs_to_clean:
        if os.path.exists(dir_name):
            print(f"Cleaning {dir_name}...")
            shutil.rmtree(dir_name)

def build_exe():
    """Build the executable"""
    print("=" * 60)
    print(f"Building {APP_NAME} v{VERSION}")
    print("=" * 60)

    # Clean previous builds
    clean_build()

    # Prepare PyInstaller command
    cmd = ["pyinstaller"] + PYINSTALLER_OPTS

    # Add icon if available
    icon = ensure_icon()
    if icon:
        cmd.extend(["--icon", icon])

    # Add main script
    cmd.append(MAIN_SCRIPT)

    print(f"\nRunning: {' '.join(cmd)}\n")

    # Run PyInstaller
    result = subprocess.run(cmd, capture_output=False)

    if result.returncode != 0:
        print("\nBuild FAILED!")
        sys.exit(1)

    print("\n" + "=" * 60)
    print("Build SUCCESSFUL!")
    print(f"Executable location: dist/{APP_NAME}/")
    print("=" * 60)

    # Create version file
    version_file = Path(f"dist/{APP_NAME}/VERSION")
    version_file.write_text(VERSION)

    return Path(f"dist/{APP_NAME}")

def create_portable_zip():
    """Create a portable ZIP distribution"""
    import zipfile

    dist_dir = Path(f"dist/{APP_NAME}")
    if not dist_dir.exists():
        print("Error: Build directory not found. Run build first.")
        return

    zip_name = f"{APP_NAME}-{VERSION}-portable.zip"
    zip_path = Path("dist") / zip_name

    print(f"\nCreating portable ZIP: {zip_path}")

    with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
        for file_path in dist_dir.rglob('*'):
            if file_path.is_file():
                arcname = file_path.relative_to(dist_dir.parent)
                zipf.write(file_path, arcname)

    print(f"Created: {zip_path}")
    print(f"Size: {zip_path.stat().st_size / (1024*1024):.2f} MB")

if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Build Windows AI executable")
    parser.add_argument("--clean", action="store_true", help="Clean build only")
    parser.add_argument("--zip", action="store_true", help="Create portable ZIP after build")
    args = parser.parse_args()

    if args.clean:
        clean_build()
        print("Clean complete.")
        sys.exit(0)

    build_exe()

    if args.zip:
        create_portable_zip()
