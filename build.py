#!/usr/bin/env python3
"""
Windows AI - Complete Build System
Builds the Windows AI application and creates installers
"""

import os
import sys
import shutil
import subprocess
import platform
from pathlib import Path
from datetime import datetime

VERSION = "2.0.0"
APP_NAME = "WindowsAI"

class Builder:
    """Complete build system for Windows AI"""

    def __init__(self):
        self.root_dir = Path(__file__).parent
        self.dist_dir = self.root_dir / "dist"
        self.build_dir = self.root_dir / "build"
        self.is_windows = platform.system() == "Windows"

    def clean(self):
        """Clean build artifacts"""
        print("Cleaning build artifacts...")
        for d in [self.dist_dir, self.build_dir]:
            if d.exists():
                shutil.rmtree(d)
        print("Clean complete")

    def install_build_deps(self):
        """Install build dependencies"""
        print("Installing build dependencies...")
        deps = ["pyinstaller", "nuitka", "wheel", "setuptools"]
        subprocess.run([sys.executable, "-m", "pip", "install"] + deps + ["-q"])

    def build_exe(self):
        """Build standalone executable"""
        print(f"\nBuilding {APP_NAME} executable...")

        pyinstaller_args = [
            sys.executable, "-m", "PyInstaller",
            "--name", APP_NAME,
            "--onedir",
            "--noconfirm",
            "--clean",
            "--add-data", f"windows_ai/plugins{os.pathsep}windows_ai/plugins",
            "--add-data", f"windows_ai/config{os.pathsep}windows_ai/config",
            "--hidden-import", "uvicorn",
            "--hidden-import", "fastapi",
            "--hidden-import", "pydantic",
            "--hidden-import", "litellm",
            "--hidden-import", "langchain",
            "--hidden-import", "chromadb",
            "--collect-all", "windows_ai",
            "windows_ai/__main__.py"
        ]

        if self.is_windows:
            pyinstaller_args.extend(["--windowed"])

        result = subprocess.run(pyinstaller_args)
        if result.returncode != 0:
            print("EXE build failed!")
            return False

        print(f"EXE built successfully: dist/{APP_NAME}/")
        return True

    def build_wheel(self):
        """Build Python wheel package"""
        print("\nBuilding Python wheel...")
        result = subprocess.run([
            sys.executable, "-m", "build", "--wheel"
        ])
        return result.returncode == 0

    def build_installer(self):
        """Build Windows installer using NSIS"""
        if not self.is_windows:
            print("NSIS installer can only be built on Windows")
            return False

        print("\nBuilding Windows installer...")
        nsis_script = self.root_dir / "installer" / "windows_ai.nsi"

        if not nsis_script.exists():
            print(f"NSIS script not found: {nsis_script}")
            return False

        # Find NSIS
        nsis_path = shutil.which("makensis")
        if not nsis_path:
            # Try common locations
            nsis_locations = [
                "C:\\Program Files (x86)\\NSIS\\makensis.exe",
                "C:\\Program Files\\NSIS\\makensis.exe"
            ]
            for loc in nsis_locations:
                if Path(loc).exists():
                    nsis_path = loc
                    break

        if not nsis_path:
            print("NSIS not found. Install from https://nsis.sourceforge.io/")
            return False

        result = subprocess.run([nsis_path, str(nsis_script)])
        return result.returncode == 0

    def create_portable_zip(self):
        """Create portable ZIP distribution"""
        import zipfile

        print("\nCreating portable ZIP...")

        exe_dir = self.dist_dir / APP_NAME
        if not exe_dir.exists():
            print("EXE directory not found. Build EXE first.")
            return False

        zip_name = f"{APP_NAME}-{VERSION}-portable.zip"
        zip_path = self.dist_dir / zip_name

        with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
            for file_path in exe_dir.rglob('*'):
                if file_path.is_file():
                    arcname = file_path.relative_to(exe_dir.parent)
                    zipf.write(file_path, arcname)

        size_mb = zip_path.stat().st_size / (1024 * 1024)
        print(f"Created: {zip_path} ({size_mb:.1f} MB)")
        return True

    def build_all(self):
        """Complete build process"""
        print("=" * 60)
        print(f"  WINDOWS AI BUILD SYSTEM - v{VERSION}")
        print("=" * 60)
        print(f"  Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"  Platform: {platform.system()} {platform.machine()}")
        print("=" * 60)

        self.clean()
        self.install_build_deps()

        success = True

        # Build EXE
        if not self.build_exe():
            success = False

        # Create portable ZIP
        if success:
            self.create_portable_zip()

        # Build installer (Windows only)
        if self.is_windows and success:
            self.build_installer()

        print("\n" + "=" * 60)
        if success:
            print("  BUILD COMPLETE!")
            print(f"  Output directory: {self.dist_dir}")
        else:
            print("  BUILD FAILED!")
        print("=" * 60)

        return success


def main():
    import argparse

    parser = argparse.ArgumentParser(description="Windows AI Build System")
    parser.add_argument("--clean", action="store_true", help="Clean only")
    parser.add_argument("--exe", action="store_true", help="Build EXE only")
    parser.add_argument("--wheel", action="store_true", help="Build wheel only")
    parser.add_argument("--installer", action="store_true", help="Build installer only")
    parser.add_argument("--zip", action="store_true", help="Create portable ZIP only")
    parser.add_argument("--all", action="store_true", help="Build everything (default)")
    args = parser.parse_args()

    builder = Builder()

    if args.clean:
        builder.clean()
    elif args.exe:
        builder.install_build_deps()
        builder.build_exe()
    elif args.wheel:
        builder.build_wheel()
    elif args.installer:
        builder.build_installer()
    elif args.zip:
        builder.create_portable_zip()
    else:
        # Default: build all
        builder.build_all()


if __name__ == "__main__":
    main()
