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
