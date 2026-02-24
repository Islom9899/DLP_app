# -*- mode: python ; coding: utf-8 -*-
"""
PyInstaller spec file for DLP + DCS Controller application.

Build command:
    pyinstaller dlp_app.spec

Output: dist/DLP_DCS_Controller.exe
"""

import os
import sys

block_cipher = None

# Detect customtkinter path for bundling theme assets
try:
    import customtkinter
    ctk_path = os.path.dirname(customtkinter.__file__)
    ctk_datas = [(ctk_path, 'customtkinter')]
except ImportError:
    ctk_datas = []

# Detect hidapi DLL for bundling
try:
    import hid
    hid_dir = os.path.dirname(hid.__file__)
    hid_dll = os.path.join(hid_dir, 'hidapi.dll')
    if os.path.exists(hid_dll):
        hid_binaries = [(hid_dll, '.')]
    else:
        hid_binaries = []
except ImportError:
    hid_binaries = []

a = Analysis(
    ['main.py'],
    pathex=[],
    binaries=hid_binaries,
    datas=ctk_datas,
    hiddenimports=[
        'hid',
        'customtkinter',
        'numpy',
        'PIL',
        'PIL.Image',
        'zarr',
        'numcodecs',
        'numcodecs.packbits',
        'drivers',
        'drivers.dlp_driver',
        'drivers.dlp_compression',
        'drivers.dlp_config',
        'drivers.dcs_controller',
        'gui',
        'gui.app',
        'gui.connection_panel',
        'gui.dlp_panel',
        'gui.dcs_panel',
        'gui.project_panel',
        'gui.status_bar',
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[
        'pywinusb',
        'matplotlib',
        'scipy',
        'pandas',
        'PyDAQmx',
        'optoMDC',
        'dask',
    ],
    noarchive=False,
    optimize=0,
)

pyz = PYZ(a.pure, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.datas,
    [],
    name='DLP_DCS_Controller',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=None,
)
