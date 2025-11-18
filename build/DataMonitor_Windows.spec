# -*- mode: python ; coding: utf-8 -*-
import os

# PyInstaller spec for the DataMonitor application (Windows build).
# This spec builds the main application (`main_frame.py`) into
# a Windows executable and collects application data
# such as `data_monitor/Config`, `i18n/`, and `docs/`.

# Resolve project root (one level up from this spec file).
# PyInstaller may execute the spec with no __file__ defined, so
# provide a safe fallback that assumes the repo layout where this
# spec lives in the `build/` directory under the project root.
if '__file__' in globals():
    spec_dir = os.path.dirname(__file__)
else:
    # When running `pyinstaller build\DataMonitor_Windows.spec` from
    # the project root, cwd == project root; assume spec is in build/.
    spec_dir = os.path.join(os.getcwd(), 'build')

BASE_DIR = os.path.abspath(os.path.join(spec_dir, '..'))

# Prefer icon in resources/icons in project root, fall back to docs
icon_path = os.path.join(BASE_DIR, 'resources', 'icons', 'datamonitor.ico')
if not os.path.exists(icon_path):
    icon_path = os.path.join(BASE_DIR, 'docs', 'datamonitor.ico')
    if not os.path.exists(icon_path):
        icon_path = None

# Data files (source absolute paths, target relative paths inside bundle)
datas = [
    (os.path.join(BASE_DIR, 'data_monitor', 'Config'), 'data_monitor/Config'),
    (os.path.join(BASE_DIR, 'i18n'), 'i18n'),
    (os.path.join(BASE_DIR, 'docs'), 'docs'),
    (os.path.join(BASE_DIR, 'resources', 'icons'), 'resources/icons'),
]

a = Analysis(
    [os.path.join(BASE_DIR, 'main_frame.py')],
    pathex=[BASE_DIR],
    binaries=[],
    datas=datas,
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
