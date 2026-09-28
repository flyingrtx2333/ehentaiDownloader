# Manga Desk desktop workspace

This Tauri + React app has separate Windows (`src/windows/`) and macOS (`src/mac/`) interfaces. They share frontend types in `src/types.ts` and the Python task engine in the repository root. See the [macOS preview](../docs/images/manga-desk-macos.png), captured with sample tasks.

## Development

Install Node.js, Rust, and Python 3.10+. From the repository root, prepare the Python environment:

```bash
python3.12 -m venv .venv
.venv/bin/python -m pip install -r requirements.txt
```

Then start the desktop app:

```bash
cd desktop
npm install
npm run tauri dev
```

Tauri selects the interface for the host OS. It prefers the repository `.venv`; set `MANGA_DESK_PYTHON` to override the interpreter. The macOS interface defaults to the system Downloads folder. Run `npm run build` to check TypeScript and build the frontend.

## Platform assets and packaging

The macOS window size is in `src-tauri/tauri.macos.conf.json`, and its layout is in `src/mac/styles.css`. Install the root Python dependencies and PyInstaller, then run `python desktop/scripts/build_engine.py` from the repository root. This creates the engine bundled by both platform configurations.

On Windows, run `npx tauri build --config src-tauri/tauri.windows.conf.json` from `desktop/`. On macOS, run `npx tauri build --config src-tauri/tauri.macos.conf.json` there, then `bash desktop/scripts/package_macos.sh` from the repository root to create the DMG. The tag workflow in `.github/workflows/release.yml` builds both macOS architectures and Windows before publishing a Release.

The selected book and arrow artwork is in `branding/`. The sidebar and favicon use `src/assets/logo-mark.png`; macOS Dock icons in `src-tauri/icons/` have transparent padding for a balanced apparent size.
