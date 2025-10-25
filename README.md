# DataMonitor v1.2.0

DataMonitor is a PySide6 desktop console that lets operations and SRE teams configure HTTP/API/server monitors without writing bespoke scripts. Version **1.2.0** streamlines release management (centralised version module), refreshes bilingual manuals, and polishes the monitor configuration workflow.

---

## Highlights (v1.2.0)

- Refined bilingual user manuals with step-by-step monitor, mail, and template workflows.
- PySide6-only GUI stack with controller/event-bus architecture.
- Template-driven notification system and per-monitor recipient overrides.

---

## Requirements

- Python 3.9+
- Windows 10+, macOS 12+, or a mainstream Linux desktop
- Dependencies declared in `requirements.txt` (`PySide6==6.7.3`, `requests==2.31.0`; `pytest` + `pytest-qt` for tests)

---

## Quick Start

```bash
git clone <repo-url> datamonitor
cd datamonitor
python -m venv .venv
source .venv/bin/activate          # Windows: .venv\Scripts\Activate.ps1
pip install -r requirements.txt
python main_frame.py
```

First launch generates `Config.ini` and `Templates.ini` under `<APIMONITOR_HOME>/Config/` (defaults to `data_monitor/Config/`). Visit **Preferences** to confirm timezone, language, theme, and log settings before starting monitors.

---

## Configuration Guide

### Application home

`APIMONITOR_HOME` (env var) controls where configuration and logs are stored. If unset, the project uses `<repo>/data_monitor/`.

- `Config/Config.ini` – monitors, logging, and mail sections.
- `Config/Templates.ini` – mail/UI/log templates.
- `Log/` – rolling log files + CSV exports.

Use `python -c "import configuration; configuration.writeconfig('<path>')"` to bootstrap a clean directory.

### Monitor definitions

Each `[MonitorX]` section in `Config.ini` maps to a monitor:

| Field | Description |
| --- | --- |
| `name` | Friendly label shown in UI, logs, and mail subjects. |
| `url` | Absolute HTTP/HTTPS URL or `host:port/path` for SERVER monitors. |
| `type` | One of `GET`, `POST`, `SERVER`. |
| `interval` | Polling interval (seconds). |
| `email` | Optional comma-separated recipients overriding the global list. |
| `payload` / `headers` | Optional JSON dictionaries for POST/custom requests. |

The Configuration wizard mirrors these fields and writes to the same file.

### Email credentials

Resolution order (all fields required):

1. **Environment variables** (`MAIL_SMTP_SERVER`, `MAIL_SMTP_PORT`, `MAIL_USERNAME`, `MAIL_PASSWORD`, `MAIL_FROM`, `MAIL_TO`).
2. **External INI** – set `MAIL_CONFIG_PATH=/secure/mail.ini` referencing a `[Mail]` section.
3. **Local Config.ini** – fallback; repository values are placeholders and must be replaced before production use.

Define `email = ...` inside individual monitors to override recipients for that task.

### Templates

`Templates.ini` exposes:

- `[mail]` (and optional `[mail[en_US]]`, etc.) – `alert_subject/body`, `recovery_subject/body`.
- `[ui]` – strings rendered in the dashboard/log feed.
- `[log]` – CSV header and textual log formatting.

After editing, click **Restore/Reload configuration** in the GUI or restart the app to apply changes.

---

## Running the Desktop Client

```bash
python main_frame.py
```

Workflow:

1. Configure SMTP + templates.
2. Add monitors via the Configuration wizard.
3. Start the scheduler from the Monitor view; the log feed echoes loaded monitors and runtime events.
4. Adjust language/theme/timezone/logging in Preferences; changes apply instantly.

Headless automation is possible via the `monitoring` package, but is outside the desktop scope.

---

## Versioning & Release Workflow

- The canonical version lives in `datamonitor/version.py` as `__version__`.
- Runtime consumers import `datamonitor.__version__` (e.g., window titles, about dialogs, logging).
- Documentation should reference the version via scripts or mention how to query it at runtime:

```bash
python -c "import datamonitor; print(datamonitor.__version__)"
```

To bump a release:

1. Update `datamonitor/version.py`.
2. Regenerate or review documentation that mentions the version (README, CHANGELOG).
3. Commit with a message such as `chore: bump version to vX.Y.Z`.

---

## Testing

```bash
pip install -r requirements.txt
pytest
```

- GUI tests rely on `pytest-qt`; they skip automatically when PySide6 is absent.
- Prefer feature tests over mocks; the application already avoids legacy PyQt5 branches.

---

## Documentation

- `docs/manual_zh.md` – Chinese end-user manual (monitor setup, email/templates, troubleshooting).
- `docs/manual_en.md` – English counterpart.
- The in-app Documentation tab renders both manuals plus the Apache 2.0 summary.

---

## License & Third-Party Notices

- Source code: [Apache License 2.0](LICENSE).
- UI runtime: [PySide6 / Qt for Python](https://doc.qt.io/qtforpython/) (LGPL v3). Distributions must keep the Qt libraries replaceable and bundle the LGPL notice.
- Other dependencies (`requests`, `PyYAML`, etc.) retain their permissive licenses.

---

## Support

- File issues or feature requests with logs/config snippets via the project tracker.
- Contributions are welcome—follow the style of existing controllers/UI modules and update documentation alongside code.
- For security-sensitive matters (SMTP credentials, production data), reach out privately instead of filing public issues.

Happy monitoring!
