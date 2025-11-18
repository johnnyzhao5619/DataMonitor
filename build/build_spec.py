from PyInstaller.building.api import BUNDLE, COLLECT, EXE, PYZ
from PyInstaller.building.build_main import Analysis
import os

# Resolve project root safely (spec may be executed without __file__)
if '__file__' in globals():
    spec_dir = os.path.dirname(__file__)
else:
    spec_dir = os.path.join(os.getcwd(), 'build')

BASE_DIR = os.path.abspath(os.path.join(spec_dir, '..'))

# 定义程序基本信息
block_cipher = None

# 收集资源文件
data_files = [
    (os.path.join(BASE_DIR, 'data_monitor', 'Config'), 'data_monitor/Config'),
    (os.path.join(BASE_DIR, 'i18n'), 'i18n'),
    (os.path.join(BASE_DIR, 'docs'), 'docs'),
    (os.path.join(BASE_DIR, 'resources', 'icons'), 'resources/icons'),
    # Include the repository LICENSE so the packaged app can display it at runtime
    (os.path.join(BASE_DIR, 'LICENSE'), 'LICENSE'),
]

# 主程序规范
a = Analysis(
    ['main_frame.py'],
    pathex=[],
    binaries=[],
    datas=data_files,
    hiddenimports=[
        'monitoring',
        'controllers',
        'ui',
        'datamonitor',
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

# 创建可执行文件
pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

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
    argv_emulation=True,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)

# 收集所有文件到一个目录
coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name='DataMonitor',
)

# 为 macOS 创建 .app 包
# macOS bundle: prefer resources/icons/datamonitor.icns
icns_path = os.path.join(BASE_DIR, 'resources', 'icons', 'datamonitor.icns')
if not os.path.exists(icns_path):
    docs_icns = os.path.join(BASE_DIR, 'docs', 'datamonitor.icns')
    if os.path.exists(docs_icns):
        icns_path = docs_icns
    else:
        icns_path = None

app = BUNDLE(
    coll,
    name='DataMonitor.app',
    icon=icns_path,
    bundle_identifier='com.johnnyzhao.datamonitor',
    version='1.2.0',
)
