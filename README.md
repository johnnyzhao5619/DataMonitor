# DataMonitor v1.3.0 (Tk UI)

DataMonitor is a Tkinter desktop console that lets operations and SRE teams configure HTTP, API, and server monitors without writing custom scripts. The Tk UI keeps business logic UI-agnostic, adds multi-workspace configuration folders, and streamlines packaging with a single PyInstaller spec.

---

## Highlights

- Tkinter shell with navigation, dashboard, configuration, documentation, and preferences views.
- Multi-workspace support: switch Config/Log roots from Preferences and keep tenants isolated.
- Safer mail delivery: no hard-coded recipients, environment and Config.ini driven only.
- Improved scheduler robustness: interval validation, defensive logging, and clearer startup errors.
- Cross-platform packaging through `build/build_spec.py` and `build/DataMonitor_Windows.spec`.

---

## Requirements

- Python 3.9 or newer
- Windows 10+, macOS 12+, or a mainstream Linux desktop
- Dependencies from `requirements.txt`

---

## Quick Start

```bash
git clone <repo-url> datamonitor
cd datamonitor
python -m venv .venv
# Windows: .venv\Scripts\Activate.ps1
# macOS/Linux: source .venv/bin/activate
pip install -r requirements.txt
python -m tkui.app
```

On first launch the app creates `Config.ini`, `Templates.ini`, and `config.workspaces.json` in the working directory. Use **Preferences -> Configuration Workspace** to add or switch workspaces (each has its own Config and Log folders).

---

## Configuration Guide

### Workspaces

- `config.workspaces.json` sits beside the executable and tracks paths plus labels.
- Each workspace contains its own `Config/` and `Log/` folders; switching isolates monitors and logs per tenant.
- Use **Browse** in Preferences to add a workspace; removing a workspace leaves files on disk.

### Application home

- `APIMONITOR_HOME` overrides the active workspace path.
- Default is the current working directory when the app first runs.
- Key files:
  - `Config/Config.ini` - monitors, logging, mail.
  - `Config/Templates.ini` - mail, UI, log templates.
  - `Log/` - rolling logs and CSV exports.

Bootstrap a clean directory with:

```bash
python -c "import configuration; configuration.writeconfig('<path>')"
```

### Monitor definitions

Each `[MonitorX]` section in `Config.ini` maps to one monitor:

| Field | Description |
| ----- | ----------- |
| `name` | Display label for UI, logs, mail subjects. |
| `url` | Full HTTP/HTTPS URL or `host:port/path` for SERVER monitors. |
| `type` | One of `GET`, `POST`, `SERVER`. |
| `interval` | Polling interval in seconds (must be positive). |
| `email` | Optional comma-separated recipients overriding global defaults. |
| `payload` / `headers` | Optional JSON dictionaries for POST/custom requests. |

### Email credentials

Resolution order (all required):

1. Environment variables: `MAIL_SMTP_SERVER`, `MAIL_SMTP_PORT`, `MAIL_USERNAME`, `MAIL_PASSWORD`, `MAIL_FROM`, `MAIL_TO`.
2. External INI: set `MAIL_CONFIG_PATH=/secure/mail.ini` with a `[Mail]` section.
3. Local `Config.ini`: fallback; replace placeholders before production.

You can override recipients per monitor with the `email` field.

### Templates

- `[mail]` (and language-specific sections) for `alert_subject/body` and `recovery_subject/body`.
- `[ui]` for status lines shown in the dashboard feed.
- `[log]` for CSV header and text log entries.

Reload configuration from the GUI or restart the app after edits.

---

## Running the Desktop Client

```bash
python -m tkui.app
```

Workflow:

1. Configure SMTP and templates.
2. Add monitors in **Configuration**.
3. Start monitoring from the **Monitor** view; the log feed shows activity.
4. Adjust language, theme, timezone, and logging in **Preferences**; changes apply live.

---

## Versioning

- Canonical version: `datamonitor/version.py` (`__version__`).
- Query at runtime: `python -c "import datamonitor; print(datamonitor.__version__)"`.
- When bumping: update `datamonitor/version.py` and docs (README, CHANGELOG), then commit (e.g., `chore: bump version to v1.3.0`).

---

## Building Executables (v1.3.0)

### Release build

```bash
python -m PyInstaller build/build_spec.py --clean --noconfirm
```

- Windows installer: `pwsh build/installer/make_installer.ps1` (updates title/metadata to 1.3.0).
- macOS/Linux: zip `dist/DataMonitor` if distributing the folder layout.
- Tk builds rely on `build/build_spec.py` or `build/DataMonitor_Windows.spec`.

### Prerequisites

```bash
pip install pyinstaller
```

### Windows build (manual)

```cmd
python -m PyInstaller build\\DataMonitor_Windows.spec --clean --noconfirm
```

Artifacts land in `dist\\DataMonitor\\`.

---

## Support and Contributions

- File issues or feature requests via your team tracker.
- Keep code DRY and UI-agnostic; prefer shared helpers in `datamonitor/core` and `datamonitor/domain`.
- Avoid mock data and hard-coded recipients in production paths.
