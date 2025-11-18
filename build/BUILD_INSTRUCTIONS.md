# DataMonitor Build Instructions

This document describes how to build DataMonitor executables for different platforms.

## Prerequisites

- Python 3.9 or later
- All dependencies installed: `pip install -r requirements.txt`
- PyInstaller: `pip install pyinstaller`

## Building for Windows

### On Windows Machine

1. Open Command Prompt or PowerShell
2. Navigate to the project root directory
3. Run the build script:
   ```cmd
   build\build_windows.bat
   ```

Or manually:

```cmd
python -m PyInstaller build\DataMonitor_Windows.spec --clean --noconfirm
```

The executable will be created in `dist\DataMonitor\DataMonitor.exe`

### Distribution Package

To create a distributable package:

1. After building, the `dist\DataMonitor\` folder contains all necessary files
2. You can zip this folder for distribution
3. Users can extract and run `DataMonitor.exe` directly

## Building for macOS

### On macOS Machine

1. Open Terminal
2. Navigate to the project root directory
3. Run:
   ```bash
   python -m PyInstaller build/DataMonitor.spec --clean --noconfirm
   ```

The application bundle will be created in `dist/DataMonitor.app`

### Distribution Package

To create a distributable package:

1. After building, create a DMG file:
   ```bash
   hdiutil create -volname "DataMonitor" -srcfolder dist/DataMonitor.app -ov -format UDZO dist/DataMonitor.dmg
   ```

## Building for Linux

### On Linux Machine

1. Open Terminal
2. Navigate to the project root directory
3. Run:
   ```bash
   python -m PyInstaller build/DataMonitor.spec --clean --noconfirm
   ```

The executable will be created in `dist/DataMonitor/DataMonitor`

## Icon Files

The project includes icon files in `resources/icons/`:

- `datamonitor.ico` - Windows icon (256x256)
- `datamonitor.icns` - macOS icon bundle
- `datamonitor_logo_icon.png` - Source PNG (1024x1024)

## Troubleshooting

### Missing Dependencies

If the build fails due to missing dependencies:

```bash
pip install -r requirements.txt
pip install pyinstaller
```

### PySide6 Issues

If you encounter PySide6-related errors:

```bash
pip uninstall PySide6
pip install PySide6==6.7.3
```

### Build Artifacts

Build artifacts are stored in:

- `dist/` - Final executable/bundle
- `build/build/` - Temporary build files
- `build/spec/` - PyInstaller spec files (if using build.py)

To clean build artifacts:

```bash
# Windows
rmdir /s /q dist build\build build\dist

# macOS/Linux
rm -rf dist build/build build/dist
```

## Version Management

The version is centrally managed in `datamonitor/version.py`. Update this file before building a new release:

```python
__version__ = "1.1.0"
```

## Release Checklist

1. Update version in `datamonitor/version.py`
2. Update `CHANGELOG.md` with release notes
3. Update `README.md` if needed
4. Build for target platform(s)
5. Test the executable
6. Create git tag: `git tag -a v1.1.0 -m "Release v1.1.0"`
7. Push changes and tag: `git push && git push --tags`
8. Create GitHub release with built executables

## Cross-Platform Notes

**Important**: PyInstaller does not support cross-compilation. You must build on the target platform:

- Windows executables must be built on Windows
- macOS bundles must be built on macOS
- Linux executables must be built on Linux

For multi-platform releases, you'll need access to each platform or use CI/CD services like GitHub Actions.
