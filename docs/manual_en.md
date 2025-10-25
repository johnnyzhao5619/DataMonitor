# DataMonitor Desktop Client – User Manual

This document focuses on day-to-day usage: how to create monitors, configure notification templates, and keep the desktop client healthy. For build or deployment topics, refer to the root README.

---

## 1. Product Overview

DataMonitor is a PySide6 desktop console that lets operations and engineering teams configure HTTP/API/server probes with minimal scripting. Core capabilities:

- **Live dashboard** that surfaces local/UTC clocks and an always-on log feed.
- **Configuration wizard** for adding GET/POST/SERVER monitors with validation and preview panels.
- **Preference center** for timezone, language, theme, and logging policies.
- **Template-driven notifications** so alerts and recoveries share consistent wording in multiple languages.
- **Documentation hub** with the Apache 2.0 license summary and this user manual.

---

## 2. Interface Tour

| Navigation tab | Purpose | Typical actions |
| --- | --- | --- |
| **Monitor** | Dashboard with clocks and rolling log | Start/stop scheduler, inspect recent events |
| **Configuration** | Monitor wizard | Add/delete monitors, edit payload & headers, preview emails |
| **Preferences** | Personalisation & logging | Change language/theme/timezone, manage log rotation |
| **Documentation** | License + manuals | Read Apache 2.0 summary, open this manual in‑app |
| **Reports** | Reserved | Placeholder for future historical analytics |

Suggested workflow: configure SMTP → add monitors → start scheduler → verify the log feed.

---

## 3. Creating Monitor Tasks

### 3.1 Shared fields

- **Name** – friendly identifier used in logs and email subjects.
- **URL** – HTTP/HTTPS address or host:port notation (SERVER type accepts `host:port/path`).
- **Type** – one of `GET`, `POST`, `SERVER`.
- **Interval** – polling interval in seconds.
- **Email** – optional comma-separated recipients that override the global list.
- **Payload / Headers** – plain text areas accepting JSON or `key=value` lines; relevant for POST/custom requests.

The wizard validates every change (blank fields, malformed hostnames, bad email formats). Errors are shown inline in the “Validation” panel.

### 3.2 GET monitors

- **Use cases**: HTTP health checks, CDN endpoints, RESTful `/status`.
- **Example**:
  - Name: `Storefront API`
  - URL: `https://api.example.com/health`
  - Interval: `60`
  - Email: `ops@example.com, dev@example.com`
- **Behaviour**: success when the HTTP status is 2xx/3xx. Failures trigger log entries and alert emails.

### 3.3 POST monitors

- **Use cases**: Webhooks that expect payloads, services requiring JSON heartbeat packets.
- **Example**:
  - URL: `https://hooks.example.com/check`
  - Payload:
    ```json
    {
      "service": "billing",
      "region": "eu-west-1"
    }
    ```
  - Headers:
    ```json
    {
      "Authorization": "Bearer <token>",
      "Content-Type": "application/json"
    }
    ```
- **Tip**: keep secrets out of the repository; inject tokens via environment variables or secure vaults and load them at runtime.

### 3.4 SERVER monitors

- **Use cases**: holistic server reachability (socket + ping + HTTP probe).
- **Example**:
  - URL: `ops.example.net:9443/status`
  - The scheduler parses protocol/host/port and runs:
    1. TCP connectivity test.
    2. Ping/ICMP (falls back to the system `ping` when raw sockets are unavailable).
    3. HTTP GET against the constructed URL (`https://ops.example.net:9443/status`).
- **Note**: ICMP requires elevated privileges on macOS/Linux. Grant the binary CAP_NET_RAW (Linux) or run with admin rights if needed.

### 3.5 Save & validate

1. Click **Save** to write changes to `Config.ini`.
2. Use **Reload configuration** if you edited the INI file manually.
3. Return to **Monitor** and press **Start**. The log feed lists every configured monitor so you can confirm it was loaded correctly.

---

## 4. Scenario Cookbook

| Scenario | Suggested type | Key settings |
| --- | --- | --- |
| Public REST API | `GET` | Poll `/health` every 30–60 s; enable per-monitor email overrides. |
| Private webhook | `POST` | Provide JSON payload + auth headers; set longer intervals for rate limiting. |
| Internal host check | `SERVER` | Supply `host:port` only; DataMonitor covers TCP + ping + HTTP. |
| Multi-region status board | Mix `GET` and `SERVER` | Duplicate monitors per region; use tags in the name (`API (cn)`). |

---

## 5. Email & Template Configuration

### 5.1 SMTP sources

DataMonitor resolves SMTP credentials in this order (all fields required):

1. **Environment variables** (preferred for production). Example:
   ```bash
   export MAIL_SMTP_SERVER=smtp.example.com
   export MAIL_SMTP_PORT=587
   export MAIL_USERNAME=alert@example.com
   export MAIL_PASSWORD='use-app-password-or-secret'
   export MAIL_FROM="DataMonitor <alert@example.com>"
   export MAIL_TO="ops@example.com,dev@example.com"
   ```
   Works well with container secrets or CI/CD pipelines.
2. **External INI file** referenced via `MAIL_CONFIG_PATH=/etc/datamonitor/mail.ini`:
   ```ini
   [Mail]
   smtp_server = smtp.internal.local
   smtp_port   = 465
   username    = infra@example.com
   password    = ${MAIL_PASSWORD}
   from_addr   = "InfraBot <infra@example.com>"
   to_addrs    = sre@example.com, oncall@example.com
   use_ssl     = true
   use_starttls = false
   ```
   Secure the file with `chmod 600`.
3. **Local Config.ini** inside `<APIMONITOR_HOME>/Config/`. The repo ships placeholders like `<SMTP_SERVER>`—replace them before starting the scheduler or a `ValueError` will be raised.

> **Smoke test**: after configuring SMTP, create a 5‑second GET monitor that targets an invalid host and confirm alert/recovery emails arrive.

### 5.2 Per-monitor recipients

- **UI**: in the Configuration form, fill the **Email** field with comma-separated addresses (e.g., `db-oncall@example.com, dba@example.com`).
- **INI**: add `email = ops@example.com` within the corresponding `[MonitorX]` section, then click “Restore configuration”.
- **Priority**: when a monitor specifies `email`, DataMonitor sends exclusively to that list and ignores the global `to_addrs`. Useful for routing alerts to different teams.

### 5.3 Editing templates

`Templates.ini` stores the notification content:

```ini
[mail]
alert_subject    = Outage Alert | {service_name}
alert_body       = Status: {status_action}\nService: {service_name}\nDetails: {event_description}\n{time_label}: {event_timestamp}
recovery_subject = Outage Recovery | {service_name}
recovery_body    = Status: {status_action}\nService: {service_name}\nDetails: {event_description}\n{time_label}: {event_timestamp}
```

- **Placeholders**: `{service_name}`, `{event_timestamp}`, `{status_action}`, `{event_description}`, `{time_label}`—all provided by the state machine.
- **Language overrides**: define `[mail[en_US]]`, `[mail[zh_CN]]`, etc., for locale-specific text:
  ```ini
  [mail[en_US]]
  alert_subject = Outage Alert | {service_name}
  alert_body    = Status: {status_action}\nService: {service_name}\nDetails: {event_description}\n{time_label}: {event_timestamp}
  ```
- **Update flow**:
  1. Pause monitoring or stop the scheduler.
  2. Edit and save Templates.ini.
  3. In-app, click **Reload configuration** (Configuration view) or restart the client.
  4. Trigger a test alert to verify previews and sent emails.

### 5.4 Language selection

- The language chosen in **Preferences → Language** decides which template section is used. English looks for `[mail[en_US]]`, otherwise falls back to `[mail]`.
- Maintain both default and locale-specific sections to avoid mixed-language notifications.
- Switching languages automatically reloads translators, theme metadata, and templates—no restart needed.

---

## 6. Logging & Troubleshooting

- **Log directory**: defaults to `<APIMONITOR_HOME>/Log/`. Configure under Preferences → Logging.
- **Rotation policy**: define file name, max size (MB, set 0 to disable), and backup count. Changes apply immediately after pressing “Save Logging Settings”.
- **Console mirroring**: enable “Console Output” to duplicate log entries to stderr for quick diagnostics.

Common issues:

1. **Scheduler won’t start** – check the log for “no valid monitors”. Verify `Config.ini` saved the expected number of `MonitorX` entries.
2. **Emails missing** – look for `monitoring.send_email` records; misconfigured ports or STARTTLS/SSL flags are the usual cause.
3. **SERVER probes fail** – verify network access manually (`ping host`, `curl https://host:port/path`) and confirm the OS allows raw ICMP when needed.

---

## 7. FAQ

1. **Can I run DataMonitor headless?** – The monitoring core can run without the GUI, but this manual covers the desktop client. See the README for headless automation guidance.
2. **Bulk import monitors?** – Edit `Config.ini` directly (sections `Monitor1`, `Monitor2`, …) then click “Reload configuration” in the UI.
3. **English vs. Chinese emails?** – Switch the app language or override templates via `[mail[en_US]]` / `[mail[zh_CN]]` sections.

---

## 8. Support

- Report bugs or enhancement requests through the project’s issue tracker with logs/config snippets.
- Contributions are welcomed under Apache License 2.0—follow the README’s contribution guidelines.
- For security-sensitive topics (credentials, production logs), contact the maintainers privately instead of posting publicly.

Happy monitoring!
