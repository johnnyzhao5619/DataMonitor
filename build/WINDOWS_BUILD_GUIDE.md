# Windows Build Guide for DataMonitor v1.1.0

This guide provides step-by-step instructions for building DataMonitor on Windows.

## Prerequisites

1. **Python 3.9 or later** installed on Windows

   - Download from: https://www.python.org/downloads/
   - Make sure to check "Add Python to PATH" during installation

2. **Git for Windows** (optional, for cloning the repository)
   - Download from: https://git-scm.com/download/win

## Step 1: Get the Source Code

### Option A: Clone from Git

```cmd
git clone https://github.com/johnnyzhao5619/DataMonitor.git
cd DataMonitor
git checkout v1.1.0
```

### Option B: Download ZIP

1. Go to: https://github.com/johnnyzhao5619/DataMonitor/releases/tag/v1.1.0
2. Download the source code ZIP
3. Extract to a folder
4. Open Command Prompt and navigate to that folder

## Step 2: Set Up Python Environment

```cmd
REM Create a virtual environment
python -m venv .venv

REM Activate the virtual environment
.venv\Scripts\activate

REM Install dependencies
pip install -r requirements.txt

REM Install PyInstaller
pip install pyinstaller
```

## Step 3: Build the Executable

### Quick Build (Recommended)

```cmd
build\build_windows.bat
```

### Manual Build

```cmd
python -m PyInstaller build\DataMonitor_Windows.spec --clean --noconfirm
```

## Step 4: Locate the Executable

After a successful build, you'll find:

- **Executable**: `dist\DataMonitor\DataMonitor.exe`
- **All required files**: `dist\DataMonitor\` folder

## Step 5: Test the Application

```cmd
cd dist\DataMonitor
DataMonitor.exe
```

The application should launch with the DataMonitor GUI.

## Step 6: Create Distribution Package

To create a distributable package:

1. Navigate to the `dist` folder
2. Zip the entire `DataMonitor` folder
3. Share the ZIP file with users

Users can:

1. Extract the ZIP file
2. Run `DataMonitor.exe` directly (no installation needed)

## Troubleshooting

### Issue: "Python is not recognized"

**Solution**: Add Python to your PATH environment variable

1. Search for "Environment Variables" in Windows
2. Edit the PATH variable
3. Add the Python installation directory (e.g., `C:\Python39\`)

### Issue: "PyInstaller not found"

**Solution**: Install PyInstaller in your virtual environment

```cmd
.venv\Scripts\activate
pip install pyinstaller
```

### Issue: "PySide6 import error"

**Solution**: Reinstall PySide6

```cmd
pip uninstall PySide6
pip install PySide6==6.7.3
```

### Issue: Build fails with missing modules

**Solution**: Ensure all dependencies are installed

```cmd
pip install -r requirements.txt --force-reinstall
```

### Issue: Executable won't run on other computers

**Possible causes**:

1. Missing Visual C++ Redistributable
   - Download from: https://aka.ms/vs/17/release/vc_redist.x64.exe
2. Windows Defender blocking the executable
   - Add an exception for the executable

## Build Output Structure

```
dist/
└── DataMonitor/
    ├── DataMonitor.exe          # Main executable
    ├── PySide6/                 # Qt libraries
    ├── data_monitor/            # Configuration templates
    ├── i18n/                    # Language files
    ├── docs/                    # Documentation
    ├── resources/               # Icons and resources
    └── [various DLLs and libraries]
```

## File Size

The complete distribution package is approximately:

- **Uncompressed**: ~150-200 MB
- **Compressed (ZIP)**: ~50-70 MB

## System Requirements

**Minimum**:

- Windows 10 or later
- 4 GB RAM
- 500 MB disk space

**Recommended**:

- Windows 10/11 (64-bit)
- 8 GB RAM
- 1 GB disk space

## Next Steps

After building:

1. Test the executable thoroughly
2. Create a GitHub release with the built executable
3. Update release notes with download links
4. Consider code signing for production releases

## Support

For issues or questions:

- GitHub Issues: https://github.com/johnnyzhao5619/DataMonitor/issues
- Documentation: See `docs/manual_en.md` or `docs/manual_zh.md`

## License

DataMonitor is licensed under Apache License 2.0.
PySide6 components are under LGPL v3 (dynamically linked).

---

**Build Date**: 2025-01-18
**Version**: 1.1.0
**Platform**: Windows 10/11 (64-bit)
