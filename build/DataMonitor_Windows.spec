# -*- mode: python ; coding: utf-8 -*-
import os

# PyInstaller spec for the DataMonitor application (Windows build).
# This spec builds the main application (`main_frame.py`) into
# a Windows executable and collects application data
# such as `data_monitor/Config`, `i18n/`, and `docs/`.

# Use the Windows icon from resources/icons/
icon_path = os.path.join('resources', 'icons', 'datamonitor.ico')
if not os.path.exists(icon_path):
    icon_path = os.path.join('docs', 'datamonitor.ico')
    if not os.path.exists(icon_path):
        icon_path = None

a = Analysis(
    ['main_frame.py'],
    pathex=[],
    binaries=[],
    datas=[
        ('data_monitor/Config', 'data_monitor/Config'),
        ('i18n', 'i18n'),
        ('docs', 'docs'),
        ('resources/icons', 'resources/icons')
    ],
    hiddenimports=[
        'monitoring',
        'controllers',
        'ui',
        'datamonitor',
        'PySide6',
        'PySide6.QtCore',
        'PySide6.QtWidgets',
        'PySide6.QtGui',
        'importlib_resources',
        'pkg_resources',
        'yaml',
        'simplejson',
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    noarchive=False,
    optimize=0,
)

pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name='DataMonitor',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=icon_path,
)

coll = COLLECT(
    exe,
    a.binaries,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name='DataMonitor',
)
