import os

# PyInstaller spec for the DataMonitor application.
# This spec builds the main application (`main_frame.py`) into
# a platform bundle/executable and collects application data
# such as `data_monitor/Config`, `i18n/`, and `docs/`.
# The spec also sets the application icon for macOS (.icns) if present.

# Prefer the icon from resources/icons/ if present, otherwise fall back to docs/
icon_candidate = os.path.join('resources', 'icons', 'datamonitor.icns')
if os.path.exists(icon_candidate):
    selected_icon = icon_candidate
else:
    fallback = os.path.join('docs', 'datamonitor.icns')
    selected_icon = fallback if os.path.exists(fallback) else None


a = Analysis(
    ['main_frame.py'],
    pathex=[],
    binaries=[],
    datas=[('data_monitor/Config', 'data_monitor/Config'), ('i18n', 'i18n'), ('docs', 'docs'), ('resources/icons', 'resources/icons')],
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
        # Common optional modules used by dependencies; including them
        # reduces missing-module warnings and improves reproducibility.
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
    icon=selected_icon,
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
app = BUNDLE(
    coll,
    name='DataMonitor.app',
    icon=selected_icon,
    bundle_identifier='com.johnnyzhao.datamonitor',
)
