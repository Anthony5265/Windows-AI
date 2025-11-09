# -*- mode: python ; coding: utf-8 -*-
# PyInstaller spec file for Windows AI Backend
# Creates a standalone executable with embedded Python and all dependencies

import os
import sys
from pathlib import Path

block_cipher = None

# Collect all Windows AI Python modules
backend_modules = [
    'windows_ai.main',
    'windows_ai.agents',
    'windows_ai.folder_watcher',
    'windows_ai.scheduler',
    'windows_ai.system_info',
    'windows_ai.explorer',
    'windows_ai.policy',
    'windows_ai.sso',
    'windows_ai.plugins.base',
    'windows_ai.plugins.registry',
    'windows_ai.plugins.loader',
    'windows_ai.plugins.builtin.web_search',
    'windows_ai.plugins.builtin.file_organizer',
    'windows_ai.plugins.builtin.system_info',
    'windows_ai.plugins.builtin.github',
    'windows_ai.plugins.builtin.code_executor',
    'windows_ai.plugins.builtin.calendar',
]

# IoT modules
iot_modules = [
    'iot.mqtt',
    'iot.matter',
    'iot.zigbee',
    'iot.home_assistant',
    'iot.automation',
    'iot.adapters.mqtt',
    'iot.adapters.zeroconf',
]

# Mesh networking modules
mesh_modules = [
    'mesh.hub',
    'mesh.node',
    'mesh.protocol',
]

# Domain AI modules
domain_modules = [
    'domains.audio_processing',
    'domains.computer_vision',
    'domains.natural_language_processing',
]

# Cloud sync modules
cloud_modules = [
    'cloud_sync.provider',
    'cloud_sync.encryption',
]

# Search modules
search_modules = [
    'search.engine',
    'search.indexer',
]

# All hidden imports (dependencies that PyInstaller might miss)
hidden_imports = backend_modules + iot_modules + mesh_modules + domain_modules + cloud_modules + search_modules + [
    # FastAPI and dependencies
    'uvicorn',
    'uvicorn.lifespan',
    'uvicorn.lifespan.on',
    'uvicorn.loops',
    'uvicorn.loops.auto',
    'uvicorn.protocols',
    'uvicorn.protocols.http',
    'uvicorn.protocols.http.auto',
    'uvicorn.protocols.websockets',
    'uvicorn.protocols.websockets.auto',
    'fastapi',
    'fastapi.responses',
    'fastapi.middleware',
    'fastapi.middleware.cors',
    'starlette',
    'starlette.responses',
    'starlette.middleware',
    'starlette.middleware.cors',

    # Pydantic
    'pydantic',
    'pydantic.fields',
    'pydantic.main',
    'pydantic_core',

    # HTTP clients
    'httpx',
    'httpx._client',
    'httpcore',

    # LiteLLM
    'litellm',
    'litellm.litellm_core_utils',

    # MQTT
    'paho.mqtt.client',

    # File watching
    'watchdog',
    'watchdog.observers',
    'watchdog.events',

    # Scheduling
    'croniter',

    # JSON/YAML
    'yaml',
    'json',

    # Async
    'asyncio',
    'anyio',

    # Logging
    'logging',
    'logging.handlers',

    # System
    'psutil',
    'platform',
    'socket',

    # Cryptography
    'cryptography',
    'cryptography.fernet',

    # Image processing
    'PIL',
    'PIL.Image',

    # Audio
    'soundfile',
    'librosa',

    # NLP
    'transformers',
    'sentence_transformers',
]

# Data files to include (will be set after root_dir is defined)
data_files = []

# Get parent directory (Windows-AI root)
import os
# SPECPATH is the full path to this .spec file
spec_file_dir = os.path.dirname(os.path.abspath(SPECPATH))
root_dir = os.path.dirname(spec_file_dir)  # Go up from installer/ to Windows-AI/

# Set data files with correct paths
data_files = [
    (os.path.join(root_dir, 'windows_ai', 'plugins', 'builtin'), 'windows_ai/plugins/builtin'),
    (os.path.join(root_dir, 'config'), 'config'),
    (os.path.join(root_dir, 'plugins', 'catalog.json'), 'plugins'),
]

# Analysis
a = Analysis(
    [os.path.join(root_dir, 'windows_ai', 'main.py')],
    pathex=[root_dir],
    binaries=[],
    datas=data_files,
    hiddenimports=hidden_imports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[
        'tkinter',  # Exclude GUI libraries we don't need
        'matplotlib',
        'pandas',
        'numpy',  # Exclude unless needed for specific features
    ],
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
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name='windows-ai-backend',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=True,  # Keep console for logging
    disable_windowed_traceback=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=os.path.join(root_dir, 'apps', 'gui', 'build', 'icon.ico') if os.path.exists(os.path.join(root_dir, 'apps', 'gui', 'build', 'icon.ico')) else None,
)
