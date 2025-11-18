import os
import platform
import sys
import subprocess


def build_app():
    """构建应用程序"""
    system = platform.system()

    # Ensure build output directories exist under build/
    build_root = 'build'
    dist_root = os.path.join(build_root, 'dist')
    work_root = os.path.join(build_root, 'build')
    spec_root = os.path.join(build_root, 'spec')
    os.makedirs(dist_root, exist_ok=True)
    os.makedirs(work_root, exist_ok=True)
    os.makedirs(spec_root, exist_ok=True)

    # 基本的 PyInstaller 命令
    # Use the current Python interpreter to run PyInstaller so that
    # the same environment (and installed packages like PySide6) are used.
    cmd = [sys.executable, '-m', 'PyInstaller', '--clean', '--noconfirm']

    # 添加数据文件
    cmd.extend(
        ['--add-data', f'data_monitor/Config{os.pathsep}data_monitor/Config'])
    cmd.extend(['--add-data', f'i18n{os.pathsep}i18n'])
    # include docs and a central resources/icons directory (preferred)
    cmd.extend(['--add-data', f'docs{os.pathsep}docs'])
    cmd.extend(['--add-data', f'resources/icons{os.pathsep}resources/icons'])

    # 添加隐藏导入
    cmd.extend(['--hidden-import', 'monitoring'])
    cmd.extend(['--hidden-import', 'controllers'])
    cmd.extend(['--hidden-import', 'ui'])
    cmd.extend(['--hidden-import', 'datamonitor'])
    # Ensure PySide6 (Qt) and common helpers are bundled
    cmd.extend(['--hidden-import', 'PySide6'])
    cmd.extend(['--hidden-import', 'PySide6.QtCore'])
    cmd.extend(['--hidden-import', 'PySide6.QtWidgets'])
    cmd.extend(['--hidden-import', 'PySide6.QtGui'])
    cmd.extend(['--hidden-import', 'importlib_resources'])
    cmd.extend(['--hidden-import', 'pkg_resources'])

    # 设置应用程序名称
    cmd.extend(['--name', 'DataMonitor'])

    # 不显示控制台窗口
    cmd.append('--windowed')

    if system == 'Darwin':  # macOS
        # 添加 .app bundle 信息
        cmd.extend([
            '--osx-bundle-identifier',
            'com.johnnyzhao.datamonitor',
        ])
        # 首选 resources/icons 下的 .icns（最好把源图放在 resources/icons/），回退到 docs/
        icon_path = 'resources/icons/datamonitor.icns'
        if not os.path.exists(icon_path):
            icon_path = 'docs/datamonitor.icns'
        if os.path.exists(icon_path):
            cmd.extend(['--icon', icon_path])
    elif system == 'Windows':
        # Windows 特定设置
        # 优先使用 resources/icons 下的 .ico（如果已生成），回退到 docs/
        ico_path = 'resources/icons/datamonitor.ico'
        if not os.path.exists(ico_path):
            ico_path = 'docs/datamonitor.ico'
        if os.path.exists(ico_path):
            cmd.extend(['--icon', ico_path])

    # 指定 PyInstaller 的输出目录（放到 build/ 下），并添加主程序文件
    cmd.extend(['--distpath', dist_root])
    cmd.extend(['--workpath', work_root])
    cmd.extend(['--specpath', spec_root])
    cmd.append('main_frame.py')

    # Try to detect PySide6 plugin directories (platforms) and include them as binaries
    try:
        import importlib
        pyside_spec = importlib.util.find_spec('PySide6')
        if pyside_spec and pyside_spec.origin:
            pyside_root = os.path.dirname(pyside_spec.origin)
            # common candidate locations for Qt plugins relative to PySide6
            candidates = [
                os.path.join(pyside_root, 'plugins'),
                os.path.join(pyside_root, 'Qt', 'plugins'),
                os.path.join(pyside_root, 'Qt6', 'plugins'),
            ]
            for cand in candidates:
                platforms = os.path.join(cand, 'platforms')
                if os.path.isdir(platforms):
                    # include all files in platforms as binaries
                    for fname in os.listdir(platforms):
                        fpath = os.path.join(platforms, fname)
                        if os.path.isfile(fpath):
                            # destination inside bundle should be plugins/platforms
                            dest = os.path.join('PySide6', 'plugins',
                                                'platforms')
                            cmd.extend(
                                ['--add-binary', f"{fpath}{os.pathsep}{dest}"])
                    break
    except Exception:
        # best-effort; continue build even if detection fails
        pass

    # 执行构建命令
    subprocess.run(cmd, check=True)


if __name__ == '__main__':
    build_app()
