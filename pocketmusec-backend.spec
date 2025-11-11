# -*- mode: python ; coding: utf-8 -*-

import sys
from pathlib import Path

block_cipher = None

# Get the project root directory
project_root = Path.cwd()

# Collect all backend modules
backend_modules = [
    'backend',
    'backend.api',
    'backend.api.routes',
    'backend.auth',
    'backend.citations',
    'backend.image_processing',
    'backend.ingestion',
    'backend.lessons',
    'backend.llm',
    'backend.pocketflow',
    'backend.repositories',
    'backend.utils',
]

# Data files to include
datas = [
    # Include the standards database directory structure
    ('data', 'data'),
]

# Hidden imports that PyInstaller might miss
hiddenimports = [
    'fastapi',
    'uvicorn',
    'pydantic',
    'starlette',
    'sqlalchemy',
    'anthropic',
    'pdfplumber',
    'PIL',
    'pytesseract',
    'backend.api.main',
    'backend.api.routes.sessions',
    'backend.api.routes.standards',
    'backend.api.routes.images',
    'backend.api.routes.settings',
]

a = Analysis(
    ['run_api.py'],
    pathex=[str(project_root)],
    binaries=[],
    datas=datas,
    hiddenimports=hiddenimports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[
        'tkinter',
        'matplotlib',
        'numpy',
        'scipy',
        'pandas',
        'jupyter',
        'notebook',
    ],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name='pocketmusec-backend',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=True,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)