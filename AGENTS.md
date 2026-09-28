# Repository Guidelines

## Project Structure & Module Organization

The Python download and PDF engines live at the repository root: `manga_downloader.py`, `pdf_generator.py`, and the GUI-independent `task_service.py`. `desktop_api.py` connects those services to the desktop app; `ui.py` is the older Tk interface. The frontend has UI entries in `desktop/src/windows/` and `desktop/src/mac/`, with shared types in `desktop/src/types.ts`. The Tauri Rust shell and configuration are in `desktop/src-tauri/`. Python tests are in `tests/`. Screenshots and other documentation assets are in `docs/images/`; desktop static assets are in `desktop/public/`.

## Build, Test, and Development Commands

Use Python 3.10+ and install root dependencies with `python -m pip install -r requirements.txt` (prefer a local `.venv`). From `desktop/`, run `npm install` and `npm run tauri dev` to launch the app; `npm run build` checks TypeScript. For releases, install PyInstaller and run `python desktop/scripts/build_engine.py` from the root before `npx tauri build --config src-tauri/tauri.windows.conf.json` or the macOS config from `desktop/`. Run `bash desktop/scripts/package_macos.sh` to make a DMG. A `v*` tag triggers the three-platform Release workflow. Run `python ui.py` for the legacy Tk interface.

## Coding Style & Naming Conventions

Follow the existing style: four-space indentation and `snake_case` for Python functions and modules; `PascalCase` for Python classes and React components; `camelCase` for TypeScript variables and functions. Keep task logic in `task_service.py` or the Python engines, and send structured events to the UI instead of importing GUI code into the service. Match nearby TypeScript formatting (two-space indentation and single quotes). No formatter or linter script is currently configured.

## Testing Guidelines

Python tests use the standard `unittest` framework. Run them from the root with `python -m unittest discover -s tests`. Name files `test_*.py` and methods `test_*`. Add tests for validation, task events, and regressions in service behavior; use temporary directories and avoid live network requests. Run `npm run build` in `desktop/` after frontend changes. There is no stated coverage threshold.

## Commit & Pull Request Guidelines

Recent commits use short subjects, sometimes with prefixes such as `feat:` or `docs:`; describe the change in an imperative, focused line. In pull requests, summarize behavior changes, list the checks run, and link a relevant issue when one exists. Include screenshots for desktop UI changes. Do not commit generated output such as `desktop/dist/`, `desktop/node_modules/`, Tauri `target/`, logs, or local configuration; these are covered by `.gitignore`.
