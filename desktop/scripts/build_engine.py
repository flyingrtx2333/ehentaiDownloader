"""Build and smoke-test the Python engine bundled with the desktop app."""

import json
import subprocess
import sys
from pathlib import Path


repository = Path(__file__).resolve().parents[2]
tauri = repository / "desktop" / "src-tauri"
engine_name = "manga-engine.exe" if sys.platform == "win32" else "manga-engine"
engine = tauri / "python-engine" / engine_name
build_dir = tauri / "target" / "pyinstaller"

subprocess.run(
    [
        sys.executable,
        "-m",
        "PyInstaller",
        "--onefile",
        "--noconfirm",
        "--clean",
        "--name",
        "manga-engine",
        "--distpath",
        str(engine.parent),
        "--workpath",
        str(build_dir),
        "--specpath",
        str(build_dir),
        str(repository / "desktop_api.py"),
    ],
    cwd=repository,
    check=True,
)

probe = subprocess.run(
    [str(engine), "download", "{}"], capture_output=True, text=True, check=False
)
if probe.returncode != 2 or json.loads(probe.stdout).get("type") != "error":
    raise SystemExit(f"Packaged engine smoke test failed: {probe.stderr or probe.stdout}")

print(f"Packaged engine ready: {engine}")
