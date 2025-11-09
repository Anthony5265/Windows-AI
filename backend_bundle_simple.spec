# -*- mode: python ; coding: utf-8 -*-
# PyInstaller spec file for Windows AI Backend
# Run this from the Windows-AI root directory:
#   python -m PyInstaller backend_bundle_simple.spec

import os

block_cipher = None

# All hidden imports
hidden_imports = [
    # Windows AI modules
    'windows_ai.main',
    'windows_ai.agents',
    'windows_ai.folder_watcher',
    'windows_ai.scheduler',
    'windows_ai.system_info',
    'windows_ai.explorer',
    'windows_ai.policy',
    'windows_ai.sso',
    'windows_ai.integrations',
    'windows_ai.plugins.base',
    'windows_ai.plugins.registry',
    'windows_ai.plugins.loader',
    'windows_ai.plugins.builtin.web_search',
    'windows_ai.plugins.builtin.file_organizer',
    'windows_ai.plugins.builtin.system_info',
    'windows_ai.plugins.builtin.github',
    'windows_ai.plugins.builtin.code_executor',
    'windows_ai.plugins.builtin.calendar',

    # IoT modules (optional)
    'iot.mqtt',
    'iot.home_assistant',
    'iot.automation',

    # Mesh modules
    'mesh.hub',
    'mesh.node',
    'mesh.protocol',

    # FastAPI and dependencies
    'uvicorn',
    'uvicorn.lifespan',
    'uvicorn.lifespan.on',
    'uvicorn.loops.auto',
    'uvicorn.protocols.http.auto',
    'uvicorn.protocols.websockets.auto',
    'fastapi',
    'fastapi.middleware.cors',
    'starlette.middleware.cors',

    # Pydantic
    'pydantic',
    'pydantic_core',

    # HTTP clients
    'httpx',
    'httpcore',

    # LiteLLM
    'litellm',

    # File watching
    'watchdog',
    'watchdog.observers',
    'watchdog.events',

    # Scheduling
    'croniter',

    # System
    'psutil',
    'asyncio',
    'anyio',
    'logging.handlers',
]

# Data files to include
data_files = [
    ('windows_ai/plugins/builtin', 'windows_ai/plugins/builtin'),
]

# Analysis
a = Analysis(
    ['windows_ai/main.py'],
    pathex=[os.getcwd()],
    binaries=[],
    datas=data_files,
    hiddenimports=hidden_imports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=['tkinter', 'matplotlib', 'pandas', 'numpy'],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

# Pure Python modules
pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

# Executable
exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name='windows-ai-backend',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=True,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)

coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name='windows-ai-backend',
)
