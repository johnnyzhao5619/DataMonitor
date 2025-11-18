# Changelog

## [v1.1.0] - 2025-01-18

### Changes

- Migrated from PyQt5 to PySide6, adopting the Qt for Python (LGPL v3) dynamic-linking approach.
- Core monitoring module now runs independently with no UI dependency.
- Improved internationalization with a bundled language-pack build tool.
- Hardened security by supporting environment variables and external credential files.
- Repository license switched to Apache License 2.0 with updated redistribution/compliance docs.
- Added logging configuration panel and documentation center to manage log policies and embed license/manual content.
- Logging panel now supports custom log directories with browsing UI; documentation center renders Markdown and swaps manuals with the active language.

### Compatibility Notes

- Requires Python 3.8 or later.
- Desktop build expects PySide6 runtime to be installed.
- Configuration file format remains backward compatible; no migration required.

### Installation

1. Install dependencies: `pip install -r requirements.txt`
2. Ensure the Qt runtime (PySide6) is available for desktop deployments.
3. Follow README.md to configure environment variables or external config files.

### Licensing

This release ships under the Apache License 2.0 (see LICENSE).
PySide6 components remain under LGPL v3 and are distributed via dynamic linking only.
