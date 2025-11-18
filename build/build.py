import os
import platform
import sys
import subprocess
from pathlib import Path


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

    # 添加数据文件（使用绝对来源路径以避免 spec 在不同 cwd 下解析错误）
    cmd.extend([
        '--add-data',
        f"{os.path.abspath('data_monitor/Config')}{os.pathsep}data_monitor/Config",
    ])
    cmd.extend([
        '--add-data',
        f"{os.path.abspath('i18n')}{os.pathsep}i18n",
    ])
    # include docs and a central resources/icons directory (preferred)
    cmd.extend([
        '--add-data',
        f"{os.path.abspath('docs')}{os.pathsep}docs",
    ])
    cmd.extend([
        '--add-data',
        f"{os.path.abspath('resources/icons')}{os.pathsep}resources/icons",
    ])

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

    # 在 Windows 下，确保存在 datamonitor.ico（优先使用 resources/icons 下的 PNG 源）
    if system == 'Windows':
        try:
            BASE_DIR = Path(__file__).resolve().parents[1]
        except Exception:
            BASE_DIR = Path(os.getcwd())

        icons_dir = BASE_DIR / 'resources' / 'icons'
        icons_dir.mkdir(parents=True, exist_ok=True)
        ico_path = icons_dir / 'datamonitor.ico'
        if not ico_path.exists():
            # Try to generate from PNG source
            src_candidates = [
                icons_dir / 'datamonitor_logo_icon.png',
                BASE_DIR / 'docs' / 'datamonitor_logo_icon.png',
            ]
            src = None
            for c in src_candidates:
                if c.exists():
                    src = c
                    break

            if src is not None:
                # Attempt to import Pillow, install if missing
                try:
                    from PIL import Image
                except Exception:
                    print('Pillow not found in environment, installing...')
                    subprocess.run(
                        [sys.executable, '-m', 'pip', 'install', 'Pillow'],
                        check=False)
                    try:
                        from PIL import Image
                    except Exception:
                        print(
                            'Failed to import Pillow after installation attempt; skipping .ico generation'
                        )
                        Image = None

                if 'Image' in locals() and Image is not None:
                    try:
                        sizes = [(256, 256), (128, 128), (64, 64), (48, 48),
                                 (32, 32), (16, 16)]
                        img = Image.open(src).convert('RGBA')
                        img.save(ico_path, sizes=sizes)
                        print(f'Generated {ico_path}')
                    except Exception as e:
                        print('Error generating ICO:', e)

    if system == 'Darwin':  # macOS
        # 添加 .app bundle 信息
        cmd.extend([
            '--osx-bundle-identifier',
            'com.johnnyzhao.datamonitor',
        ])
        # 首选 resources/icons 下的 .icns（最好把源图放在 resources/icons/），回退到 docs/
        # 如果不存在 .icns，尝试从 PNG 生成（优先使用 Pillow；在 macOS 上回退到 iconutil）
        try:
            BASE_DIR = Path(__file__).resolve().parents[1]
        except Exception:
            BASE_DIR = Path(os.getcwd())

        icons_dir = BASE_DIR / 'resources' / 'icons'
        icons_dir.mkdir(parents=True, exist_ok=True)
        icns_path = icons_dir / 'datamonitor.icns'
        if not icns_path.exists():
            # try to find png source
            png_candidates = [
                icons_dir / 'datamonitor_logo_icon.png',
                icons_dir / 'datamonitor_logo_standard.png',
                BASE_DIR / 'docs' / 'datamonitor_logo_icon.png',
            ]
            src = None
            for p in png_candidates:
                if p.exists():
                    src = p
                    break

            if src is not None:
                # attempt Pillow ICNS save
                try:
                    from PIL import Image

                    img = Image.open(src)
                    try:
                        img.save(icns_path, format='ICNS')
                        print(f'Generated {icns_path} using Pillow')
                    except Exception:
                        # Pillow might not support ICNS on some platforms; fall back
                        raise
                except Exception:
                    # fallback: on macOS create .iconset and run iconutil if available
                    try:
                        import shutil

                        iconset_dir = icons_dir / 'datamonitor.iconset'
                        if iconset_dir.exists():
                            shutil.rmtree(iconset_dir)
                        iconset_dir.mkdir()
                        # create required sizes
                        sizes = [
                            (16, 'icon_16x16.png'),
                            (32, 'icon_16x16@2x.png'),
                            (32, 'icon_32x32.png'),
                            (64, 'icon_32x32@2x.png'),
                            (128, 'icon_128x128.png'),
                            (256, 'icon_128x128@2x.png'),
                            (256, 'icon_256x256.png'),
                            (512, 'icon_256x256@2x.png'),
                            (512, 'icon_512x512.png'),
                            (1024, 'icon_512x512@2x.png'),
                        ]
                        from PIL import Image

                        src_img = Image.open(src).convert('RGBA')
                        for size, name in sizes:
                            out = iconset_dir / name
                            src_img.resize((size, size),
                                           Image.LANCZOS).save(out)

                        # run iconutil if available
                        if shutil.which('iconutil'):
                            subprocess.run([
                                'iconutil', '-c', 'icns',
                                str(iconset_dir), '-o',
                                str(icns_path)
                            ],
                                           check=False)
                            if icns_path.exists():
                                print(f'Generated {icns_path} using iconutil')
                        else:
                            print(
                                'iconutil not found; cannot convert .iconset to .icns automatically'
                            )
                    except Exception as e:
                        print('Failed to generate .icns:', e)

        # final: prefer generated icns in resources, else docs fallback
        if icns_path.exists():
            cmd.extend(['--icon', str(icns_path)])
        else:
            docs_icns = Path('docs') / 'datamonitor.icns'
            if docs_icns.exists():
                cmd.extend(['--icon', str(docs_icns)])
    elif system == 'Windows':
        # Windows 特定设置
        # 优先使用 resources/icons 下的 .ico（如果已生成），回退到 docs/
        # prefer the ico we may have generated above (absolute)
        candidate_ico = icons_dir / 'datamonitor.ico'
        if candidate_ico.exists():
            cmd.extend(['--icon', str(candidate_ico)])
        else:
            docs_ico = Path('docs') / 'datamonitor.ico'
            if docs_ico.exists():
                cmd.extend(['--icon', str(docs_ico)])

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
