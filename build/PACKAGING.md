# Packaging layout and guidance

This repository consolidates packaging-related files under the `build/`
directory. Keep only the authoritative spec(s) and helper scripts there.

Files of interest
- `build/DataMonitor.spec` — authoritative PyInstaller spec for building the
  DataMonitor app. Use this in CI or locally: `python -m PyInstaller build/DataMonitor.spec`.
- `build/build_spec.py` — (optional) alternate programmatic helper kept for
  advanced packaging flows.
- `build.py` — convenience script that invokes PyInstaller; it will prefer
  icons under `resources/icons/` and places outputs under `build/dist/`,
  `build/build/`, and `build/spec/` when used.

Best practices
- Keep generated artefacts out of the repo (`dist/`, `build/`, generated
  `.ico`/`.icns` files). Add CI steps that create icons and run the spec.
- Put source PNGs in `resources/icons/` and generate `.ico`/`.icns` during
  the build job to ensure deterministic outputs.

Quick local build steps
```bash
source .venv/bin/activate
# generate icons (if needed)
python tools/gen_ico.py
iconutil -c icns resources/icons/datamonitor.iconset -o resources/icons/datamonitor.icns
# run PyInstaller using the venv python
python -m PyInstaller build/DataMonitor.spec --clean --noconfirm
```
