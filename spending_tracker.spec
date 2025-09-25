# -*- mode: python ; coding: utf-8 -*-

"""
PyInstaller Specification File for Spending Tracker GUI

This creates a standalone Windows executable with the custom icon embedded.
"""

import sys
from pathlib import Path

# Get the current directory
current_dir = Path.cwd()

block_cipher = None

a = Analysis(
    ['src/main.py'],
    pathex=[str(current_dir)],
    binaries=[],
    datas=[
        # Include configuration files
        ('config', 'config'),
        # Include data directory (for local storage)
        ('data', 'data'),
        # Include assets (icons, etc.)
        ('assets', 'assets'),
    ],
    hiddenimports=[
        # PySide6 modules that might not be auto-detected
        'PySide6.QtCore',
        'PySide6.QtGui', 
        'PySide6.QtWidgets',
        'PySide6.QtCharts',
        # Google API modules (if used)
        'google',
        'google.auth',
        'google.auth.transport.requests',
        'googleapiclient',
        'googleapiclient.discovery',
        # Email modules
        'smtplib',
        'email',
        'email.mime',
        'email.mime.text',
        'email.mime.multipart',
        # JSON and YAML handling
        'json',
        'yaml',
        # Date/time modules
        'datetime',
        'dateutil',
        # Other potential modules
        'pathlib',
        'configparser',
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[
        # Exclude unnecessary modules to reduce size
        'tkinter',
        'matplotlib',
        'numpy',
        'scipy',
        'pandas',
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
    name='SpendingTracker',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,  # Set to False for GUI application (no console window)
    disable_windowed_traceback=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    # Custom icon for the executable
    icon='assets/windows_desktop_icon.ico',
    # Version information
    version_file=None,  # Could add version info file later
)

# Optional: Create an installer/distribution directory
coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name='SpendingTracker'
)