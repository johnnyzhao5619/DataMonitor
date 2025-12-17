# API Monitor (PyQt)

PyQt5 desktop tool to monitor configured endpoints, send alerts, and log results.

## Requirements
- Python 3.10+ (Windows recommended)
- Install dependencies: `pip install -r requirements.txt`

## Quick start
1) Configure monitors in `API Monitor/Config/MonitorList.ini` and general/app settings in `API Monitor/Config/Config.ini`.
2) Run the GUI: `python main_frame.py`
3) Use the Settings dialog (gear icon) to adjust SMTP, templates, timezone, and monitor items.

## Build (PyInstaller)
- Generate binaries: `pyinstaller main_frame.spec`
- Artifacts: `dist/` (output) and `build/` (intermediate).

## Configuration basics
- General: app name, version, timezone in `Config.ini`.
- Logging: log level/path in `Config.ini` (`./API Monitor/` by default).
- Monitors: endpoints, intervals, headers, payload in `MonitorList.ini`.
- Mail templates: outage/restored/log line templates in `Config.ini` under `[Templates]`.

## Notes
- Current release: v1.3.0 (branch: `PyQt`).
- No automated tests included; manual validation recommended after config changes.
