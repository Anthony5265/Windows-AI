#!/usr/bin/env python3
"""
Windows AI - Working Build Script
Creates a functional standalone executable
"""

import os
import sys
import shutil
import subprocess
from pathlib import Path

APP_NAME = "WindowsAI"
VERSION = "2.0.0"

def check_pyinstaller():
    """Check if PyInstaller is installed"""
    try:
        import PyInstaller
        print(f"✓ PyInstaller {PyInstaller.__version__} found")
        return True
    except ImportError:
        print("✗ PyInstaller not found")
        print("\nInstalling PyInstaller...")
        subprocess.run([sys.executable, "-m", "pip", "install", "pyinstaller"], check=True)
        return True

def clean_build():
    """Clean previous builds"""
    dirs_to_clean = ["build", "dist", "__pycache__"]
    for dir_name in dirs_to_clean:
        if os.path.exists(dir_name):
            print(f"Cleaning {dir_name}...")
            shutil.rmtree(dir_name, ignore_errors=True)

def create_minimal_entry_point():
    """Create a minimal entry point that works"""
    entry_script = Path("windows_ai_entry.py")
    
    content = '''#!/usr/bin/env python3
"""Windows AI Entry Point"""
import sys
import os

# Add the application directory to path
if getattr(sys, 'frozen', False):
    application_path = sys._MEIPASS
else:
    application_path = os.path.dirname(os.path.abspath(__file__))

sys.path.insert(0, application_path)

# Run the simple version
from windows_ai_simple import main

if __name__ == "__main__":
    main()
'''
    
    entry_script.write_text(content)
    print(f"✓ Created entry point: {entry_script}")
    return entry_script

def build_minimal():
    """Build minimal working executable"""
    print("=" * 60)
    print(f"Building {APP_NAME} v{VERSION} - Minimal Working Version")
    print("=" * 60)
    
    # Check PyInstaller
    check_pyinstaller()
    
    # Clean
    clean_build()
    
    # Create entry point
    entry_script = create_minimal_entry_point()
    
    # Minimal PyInstaller options
    cmd = [
        "pyinstaller",
        "--name", APP_NAME,
        "--onefile",  # Single exe
        "--console",  # Keep console for now
        "--noconfirm",
        "--clean",
        # Include the simple script
        "--add-data", "windows_ai_simple.py;.",
        # Hidden imports
        "--hidden-import", "asyncio",
        "--hidden-import", "logging",
        str(entry_script)
    ]
    
    # Add icon if exists
    icon_path = Path("assets/icon.ico")
    if icon_path.exists():
        cmd.extend(["--icon", str(icon_path)])
    
    print(f"\nRunning PyInstaller...")
    print(f"Command: {' '.join(cmd)}\n")
    
    result = subprocess.run(cmd)
    
    if result.returncode == 0:
        print("\n" + "=" * 60)
        print("✓ Build SUCCESSFUL!")
        print(f"✓ Executable: dist/{APP_NAME}.exe")
        print("=" * 60)
        
        # Test the exe
        print("\nTesting executable...")
        test_result = subprocess.run(
            [f"dist/{APP_NAME}.exe", "--version"],
            capture_output=True,
            text=True
        )
        
        if test_result.returncode == 0:
            print("✓ Executable works!")
            print(f"Output: {test_result.stdout}")
        else:
            print("✗ Executable test failed")
            print(f"Error: {test_result.stderr}")
        
        return True
    else:
        print("\n✗ Build FAILED!")
        return False

def build_with_dependencies():
    """Build with FastAPI and other dependencies"""
    print("=" * 60)
    print(f"Building {APP_NAME} v{VERSION} - Full Version")
    print("=" * 60)
    
    check_pyinstaller()
    clean_build()
    entry_script = create_minimal_entry_point()
    
    cmd = [
        "pyinstaller",
        "--name", f"{APP_NAME}_Full",
        "--onefile",
        "--console",
        "--noconfirm",
        "--clean",
        "--add-data", "windows_ai_simple.py;.",
        # Core dependencies
        "--hidden-import", "asyncio",
        "--hidden-import", "logging",
        "--hidden-import", "fastapi",
        "--hidden-import", "uvicorn",
        "--hidden-import", "pydantic",
        "--hidden-import", "starlette",
        "--hidden-import", "openai",
        "--collect-all", "fastapi",
        "--collect-all", "uvicorn",
        str(entry_script)
    ]
    
    icon_path = Path("assets/icon.ico")
    if icon_path.exists():
        cmd.extend(["--icon", str(icon_path)])
    
    print(f"\nRunning PyInstaller with full dependencies...")
    result = subprocess.run(cmd)
    
    if result.returncode == 0:
        print("\n" + "=" * 60)
        print("✓ Full build SUCCESSFUL!")
        print(f"✓ Executable: dist/{APP_NAME}_Full.exe")
        print("=" * 60)
        return True
    else:
        print("\n✗ Full build FAILED!")
        return False

if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Build Windows AI")
    parser.add_argument("--minimal", action="store_true", help="Build minimal version")
    parser.add_argument("--full", action="store_true", help="Build full version with dependencies")
    parser.add_argument("--clean", action="store_true", help="Clean only")
    
    args = parser.parse_args()
    
    if args.clean:
        clean_build()
        print("✓ Clean complete")
        sys.exit(0)
    
    if args.full:
        success = build_with_dependencies()
    elif args.minimal:
        success = build_minimal()
    else:
        print("Building both versions...\n")
        minimal_ok = build_minimal()
        print("\n")
        full_ok = build_with_dependencies()
        success = minimal_ok or full_ok
    
    sys.exit(0 if success else 1)
