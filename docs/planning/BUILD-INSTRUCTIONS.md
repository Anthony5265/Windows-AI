# Windows AI - Build Instructions

## Overview
Your Windows AI project has both a Python backend and an Electron GUI. This document provides instructions for building the executable files.

## What's Been Completed

✅ Python backend built successfully at: `dist/WindowsAI/`
✅ Icon files prepared in: `apps/gui/build/`
✅ Build scripts created

## Building the Complete Application

### Option 1: Python Backend Only (Completed ✓)
The Python backend has been successfully built using PyInstaller.

**Location**: `dist/WindowsAI/`

**To run**: Execute `dist/WindowsAI/WindowsAI.exe`

### Option 2: Simple Portable Build (Recommended)

1. **Build the Python backend** (Already done!):
   ```bash
   python build_exe.py
   ```

2. **Package the Electron GUI**:
   ```bash
   cd apps/gui
   npx electron-packager . WindowsAI --platform=win32 --arch=x64 --out=../../dist-simple --overwrite --icon=build/icon.ico --asar
   ```

3. **Create portable package**:
   - Copy contents from `dist/WindowsAI/`
   - Copy contents from `dist-simple/WindowsAI-win32-x64/`
   - Compress into a ZIP file

### Option 3: Full Installer Build (Advanced)

The electron-builder configuration is set up but may encounter Windows-specific issues with antivirus software blocking app-builder.exe.

**If you want to try this**:

1. **Temporarily disable Windows Defender/Antivirus** (This is the common cause)

2. **Run the build**:
   ```bash
   cd apps/gui
   npm run build:win
   ```

3. **Expected output**:
   - NSIS Installer: `apps/gui/dist/WindowsAI-{version}-{arch}.exe`
   - Portable version: `apps/gui/dist/WindowsAI-Portable-{version}-{arch}.exe`

## Common Issues

### Issue: "app-builder.exe ENOENT"
**Cause**: Windows Defender or antivirus software is blocking app-builder.exe

**Solutions**:
1. Add exception in Windows Defender for `node_modules` folder
2. Use Option 2 (Simple Portable Build) instead
3. Temporarily disable antivirus during build

### Issue: Missing dependencies
**Solution**:
```bash
cd C:\Users\antho\Windows-AI-main
npm install
```

## Build Scripts

### build-simple.bat
A simple batch script that builds both the Python backend and packages the Electron GUI:
```bash
build-simple.bat
```

### build_exe.py
Builds only the Python backend:
```bash
python build_exe.py
```

**Options**:
- `python build_exe.py --clean` - Clean build artifacts
- `python build_exe.py --zip` - Create portable ZIP after build

## Directory Structure

```
dist/
├── WindowsAI/           # Python backend executable
│   ├── WindowsAI.exe    # Main executable
│   └── ...              # Dependencies

apps/gui/dist/           # Electron installer (if Option 3 works)
└── WindowsAI-*.exe      # Installer

dist-simple/             # Simple portable build (Option 2)
└── WindowsAI-win32-x64/ # Electron app
    └── WindowsAI.exe    # GUI executable
```

## Next Steps

1. **Test the Python backend**: Run `dist/WindowsAI/WindowsAI.exe` to verify it works
2. **Choose your build method**: Use Option 2 for a simple portable build
3. **Distribute**: Package everything into a ZIP file or use the NSIS installer

## Troubleshooting

If you encounter issues:
1. Check that Python 3.12 is installed
2. Verify Node.js is installed (v18+)
3. Ensure all dependencies are installed: `npm install`
4. Check Windows Defender settings
5. Run builds from a non-admin terminal (PyInstaller recommendation)

## Configuration Files

- `build_exe.py` - Python backend build configuration
- `apps/gui/electron-builder.yml` - Electron installer configuration
- `apps/gui/package.json` - Electron app metadata
- `apps/gui/build/` - Icon and installer resources
