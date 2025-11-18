@echo off
REM Build script for DataMonitor on Windows
REM This script should be run from the project root directory

echo Building DataMonitor for Windows...
echo.

REM Check if Python is available
python --version >nul 2>&1
if errorlevel 1 (
    echo Error: Python is not installed or not in PATH
    exit /b 1
)

REM Check if PyInstaller is installed
python -m PyInstaller --version >nul 2>&1
if errorlevel 1 (
    echo PyInstaller not found. Installing...
    python -m pip install pyinstaller
)

REM Clean previous builds
if exist "dist" rmdir /s /q dist
if exist "build\build" rmdir /s /q build\build
if exist "build\dist" rmdir /s /q build\dist

REM Ensure Windows .ico exists (generate from PNG if needed)
if not exist "resources\icons\datamonitor.ico" (
    echo datamonitor.ico not found, attempting to generate from PNG...
    REM Ensure Pillow is installed to run the icon generator
    python -c "import PIL" >nul 2>&1
    if errorlevel 1 (
        echo Pillow not found. Installing Pillow...
        python -m pip install Pillow >nul 2>&1
        if errorlevel 1 (
            echo Failed to install Pillow. Icon generation will be skipped.
        ) else (
            python tools\gen_ico.py >nul 2>&1
            if errorlevel 1 (
                echo Failed to generate datamonitor.ico. Make sure PNG exists in resources\icons
            ) else (
                echo Generated resources\icons\datamonitor.ico
            )
        )
    ) else (
        REM Pillow already installed, try generate icon directly
        python tools\gen_ico.py >nul 2>&1
        if errorlevel 1 (
            echo Failed to generate datamonitor.ico. Make sure PNG exists in resources\icons
        ) else (
            echo Generated resources\icons\datamonitor.ico
        )
    )
)

REM Build using the Windows spec file
echo.
echo Running PyInstaller...
python -m PyInstaller build\DataMonitor_Windows.spec --clean --noconfirm

if errorlevel 1 (
    echo.
    echo Build failed!
    exit /b 1
)

echo.
echo Build completed successfully!
echo Executable location: dist\DataMonitor\DataMonitor.exe
echo.
pause
